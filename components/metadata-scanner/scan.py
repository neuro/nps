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

def handle_dataset(dataset, hashes):
    missing = False
    meta_root = '/datasets/{}/{}/{}/{}/{}/meta'.format(dataset[0], dataset[1], dataset[2], dataset[3], dataset)
    for hash in hashes:
        meta_path = os.path.join(meta_root, hash)
        if not os.path.exists(meta_path):
            logging.info(f"Generating missing metadata collection {hash} for dataset {dataset}")
            missing = True
    if missing:
        info = {'dataset': dataset, 'change': 'Missing metadata detected'}
        r.publish('dataset-changes', json.dumps(info))

collections = load_collections()
hashes = []
for hash, collection in collections.items():
    if 'generator' not in collection:
        continue
    if 'image' not in collection['generator']:
        continue
    hashes.append(hash)
paths = glob('/datasets/*/*/*/*/*')
for path in paths:
    handle_dataset(os.path.basename(path), hashes)
