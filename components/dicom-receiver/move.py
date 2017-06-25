#!/usr/bin/python3
import logging, dicom, hashlib, os, shutil, sys, redis, json
base = '/datasets'
path = sys.argv[1]
file = dicom.read_file(path)
siid = file.SeriesInstanceUID
hash = hashlib.sha1(siid.encode('utf-8')).hexdigest().lower()
root = os.path.join(base, hash[0], hash[1], hash[2], hash[3], hash)
data = os.path.join(root, 'data')
meta = os.path.join(root, 'meta')
soid = file.SOPInstanceUID
name = '{}.dcm'.format(soid)
full = os.path.join(data, name)

if not os.path.exists(root):
    os.makedirs(root, exist_ok=True) # Multiple instances may run at the same time

if os.path.isfile(full):
    logging.warning("File already exists at {}".format(full))
    os.remove(path) # Delete temporary file if target file already exists.
else:
    os.makedirs(meta, exist_ok=True)
    os.makedirs(data, exist_ok=True)
    shutil.move(path, full)

r = redis.StrictRedis(host='nps-redis', port=6379, db=0)
info = {'dataset': hash, 'change': 'Dataset touched by DICOM receiver'}
r.publish('dataset-changes', json.dumps(info))
