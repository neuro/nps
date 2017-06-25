from elasticsearch import Elasticsearch
from datetime import datetime
import traceback
import hashlib
import logging
import string
import redis
import time
import json
import sys
import os

r = redis.StrictRedis(host='nps-redis', port=6379, db=0)
e = Elasticsearch(["elasticsearch-master"], maxsize=25)

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
    return meta_path

def index_metadata(dataset_id):
    path = metadata_path(dataset_id)
    if not os.path.exists(path):
        return
    for collection_hash in os.listdir(path):
        if len(collection_hash) != 40:
            continue
        collection_path = os.path.join(path, collection_hash)
        body = {"@timestamp": datetime.fromtimestamp(os.path.getctime(collection_path))}
        for filename in os.listdir(collection_path):
            file_path = os.path.join(collection_path, filename)
            with open(file_path) as file:
                data = json.load(file, parse_int=float)
                if isinstance(data, dict):
                    body.update(data)
                else:
                    body[filename] = data
        e.index(index=f"nps-metadata-{collection_hash}", doc_type=collection_hash, id=dataset_id, body=body)

count = 0
limit = int(os.environ.get("DATASET_LIMIT", 1000))
while count < limit:
    q, s = r.blpop('metadata-index')
    count += 1
    try:
        data = json.loads(s)
        dataset_id = data['dataset']
        index_metadata(dataset_id)
    except:
        logging.error(traceback.print_exc())
        pass
