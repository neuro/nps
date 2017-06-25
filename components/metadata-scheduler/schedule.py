import os, json, redis, hashlib, logging, traceback
from glob import glob

r = redis.StrictRedis(host='nps-redis', port=6379, db=0)

def hash_collection(collection):
    name = collection['name']
    version = collection['version']
    if not isinstance(version, int):
        raise TypeError("Version must be an integer.")
    version_string = f"{name}:{version}"
    return hashlib.sha1(version_string.encode('utf8')).hexdigest().lower()

def load_collections():
    collections = {}
    for filename in glob("/definitions/*.json"):
        with open(filename) as file:
            collection = json.load(file)
            hash = hash_collection(collection)
            collections[hash] = collection
    return collections

def schedule_meta_job(dataset, collection):
    if 'generator' not in collection:
        return
    generator = collection['generator']
    if 'image' not in generator:
        return
    job = {
        'version': 2,
        'image': generator['image'],
        'command': generator['command'],
        'dataset': dataset,
        'collection': hash_collection(collection)
    }
    r.rpush('metadata-jobs', json.dumps(job))

def handle_dataset(dataset):
    collections = load_collections()
    root = '/datasets/{}/{}/{}/{}/{}'.format(dataset[0], dataset[1], dataset[2], dataset[3], dataset)
    meta = os.path.join(root, 'meta')
    for hash, collection in collections.items():
        if not os.path.exists(os.path.join(meta, hash)):
            schedule_meta_job(dataset, collection)
    
p = r.pubsub(ignore_subscribe_messages=True)
p.subscribe('dataset-changes')
for message in p.listen():
    try:
        data = json.loads(message['data'])
        if data['change'] != 'Metadata added by job execution':
            dataset = data['dataset']
            handle_dataset(dataset)
    except:
        logging.error(traceback.print_exc())
        pass
    