from glob import glob
import redis, json, os

r = redis.StrictRedis(host='nps-redis', port=6379, db=0)

def handle_dir(path):
    datasets = os.listdir(path)
    for dataset in datasets:
        print(dataset)
        index_request = {"dataset": dataset}
        r.rpush("metadata-index", json.dumps(index_request))

paths = glob("/datasets/*/*/*/*")
for path in paths:
    handle_dir(path)
