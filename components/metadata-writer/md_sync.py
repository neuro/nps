import traceback
import hashlib
import logging
import string
import redis
import json
import sys
import os

r = redis.StrictRedis(host='nps-redis', port=6379, db=0)

def hash_collection(collection):
    name = collection['name']
    version = collection['version']
    if not isinstance(version, int):
        raise TypeError("Version must be an integer.")
    version_string = f"{name}:{version}"
    return hashlib.sha1(version_string.encode('utf8')).hexdigest().lower()

def metadata_path(dataset_id):
    if (len(dataset_id) != 40) or (not all(c in string.hexdigits for c in dataset_id)):
        raise ValueError(f"{dataset_id} is not a valid dataset id.")
    root = '/datasets/{}/{}/{}/{}'.format(dataset_id[0], dataset_id[1], dataset_id[2], dataset_id[3])
    path = os.path.join(root, dataset_id) # Metadata will only be added to complete datasets (no leading dot)
    if not os.path.exists(path):
        raise SystemError(f"Path {path} for dataset {dataset_id} does not exist.")
    meta_path = os.path.join(path, 'meta')
    os.makedirs(meta_path, exist_ok=True)
    return meta_path

def handle_task(string):
    task = json.loads(string)
    collection = task['collection']
    dataset_id = task['dataset']
    new_values = task['values']
    meta_path = metadata_path(dataset_id)
    hash = hash_collection(collection)
    path = os.path.join(meta_path, hash)
    os.makedirs(path, exist_ok=True)
    for k, v in new_values.items():
        filename = os.path.join(path, k)
        value = json.dumps(v)
        with open(filename, "w") as file:
            file.write(value)
    info = {'dataset': dataset_id, 'change': 'metadata written'}
    r.publish('dataset-changes', json.dumps(info))

while True:
    q, s = r.blpop('metadata-changes')
    try:
        handle_task(s)
    except:
        logging.error(traceback.print_exc())
        pass