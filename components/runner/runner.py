import docker, redis, json, os, shutil, hashlib, logging, traceback

r = redis.StrictRedis(host='nps-redis', port=6379, db=0)
d = docker.from_env(version='auto')

def temp_path(dataset_id):
    return '/nps/datasets/{}/{}/{}/{}/.{}'.format(dataset_id[0], dataset_id[1], dataset_id[2], dataset_id[3], dataset_id)

def final_path(dataset_id):
    return '/nps/datasets/{}/{}/{}/{}/{}'.format(dataset_id[0], dataset_id[1], dataset_id[2], dataset_id[3], dataset_id)

def hash_dataset_job(image, command, mounts):
    ''' The image parameter must be a docker.Image object '''
    desc = {'version': 2, 'image': image.id, 'command': command, 'mounts': mounts}
    data = json.dumps(desc, sort_keys=True, indent=4, separators=(',', ': '))
    return hashlib.sha1(data.encode('utf8')).hexdigest().lower()

def run_container(image, command, name, volumes):
    container = d.containers.run(image, command=command, name=name, volumes=volumes, detach=True)
    container.wait()
    try:
        container.remove(v=True)
        d.containers.prune()
        d.images.prune()
    except:
        pass

def schedule_metadata_job(job):
    if job['version'] != 2:
        raise Exception("Only version 2 metadata jobs are supported by this runner")
    image = job['image']
    command = job['command'] if job['command'] != '' else None
    data_id = job['dataset']
    path_data = os.path.join(final_path(data_id), 'data')
    if not os.path.exists(path_data):
        raise Exception("Metadata can no be created for non-existing dataset")
    meta_id = job['collection']
    path_meta = os.path.join(final_path(data_id), 'meta', meta_id)
    if os.path.exists(path_meta):
        raise Exception(f"Metadata collection {meta_id} already exists for {data_id}")
    os.makedirs(path_meta, exist_ok=True)
    name = f'nps-meta-{data_id}-{meta_id}'
    volumes = {
        path_data: {
            'bind': '/input',
            'mode': 'ro'
        },
        path_meta: {
            'bind': '/output',
            'mode': 'rw'
        }
    }
    # Image is passed as a string here as it is assumed to be constant for metadata creators
    run_container(image, command, name, volumes)
    info = {'dataset': data_id, 'change': 'Metadata added by job execution'}
    r.rpush("metadata-index", json.dumps(info))
    r.publish('dataset-changes', json.dumps(info))

def schedule_dataset_job(job):
    if job['version'] != 2:
        raise Exception("Only version 2 jobs are supported by this runner")
    image = d.images.pull(job['image'])
    command = job['command'] if job['command'] != '' else None
    mounts = job['mounts']
    hash = hash_dataset_job(image, command, mounts)
    name = 'nps-job-' + hash
    path_out = final_path(hash)
    if os.path.exists(path_out):
        raise Exception("Equivalent job already ran")
    path_tmp = temp_path(hash)
    if os.path.exists(path_tmp) and job.get('force', False):
        shutil.rmtree(path_tmp)
    os.makedirs(os.path.join(path_tmp, 'data'))
    volumes = {}
    volumes[path_tmp] = {'bind': '/output', 'mode': 'rw'}
    for mount in mounts:
        if mount['type'] == 'dataset':
            path = os.path.join(final_path(mount['name']), 'data') 
            if not os.path.exists(path):
                raise Exception(f"No dataset available at {path}")
            volumes[path] = {'bind': mount['path'], 'mode': 'ro'}
        else:
            raise ValueError('Unsupported mount type for job')
    run_container(image, command, name, volumes)
    shutil.move(path_tmp, path_out)
    info = {'dataset': hash, 'change': 'Dataset created by job execution'}
    r.publish('dataset-changes', json.dumps(info))
    
while True:
    q, job = r.blpop(('dataset-jobs', 'metadata-jobs'), 0)
    logging.info(f"Received job from {q}")
    try:
        data = json.loads(job)
        if q == b'dataset-jobs':
            schedule_dataset_job(data)
        elif q == b'metadata-jobs':
            schedule_metadata_job(data)
    except:
        logging.error(traceback.print_exc())
        pass
