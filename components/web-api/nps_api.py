import os, hug, zipfile, hashlib
from io import BytesIO

class Dataset(object):
    def __init__(self, dataset_id):
        self.id = dataset_id

    @property
    def mutable(self):
        base = os.path.basename(self.path)
        return base.startswith('.')
        
    @mutable.setter
    def mutable(self, desired_mutable):
        if os.path.exists(self.path(final=True)):
            raise Exception("An immutable dataset of the same name already exists")
        if not desired_mutable and self.mutable:
            os.rename(self.path, self.path(final=True))
        else:
            raise Exception("Immutable datasets cannot be opened again.")
            
    def add_file(self, filename, content):
        if not self.mutable:
            raise Exception("This is an immutable dataset.")
        path = self.get_path(filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as file:
            file.write(content)
        
    def get_path(self, rel_path):
        data = os.path.join(self.path, 'data')
        path = os.path.join(data, rel_path)
        path = os.path.normpath(path)
        if not path.startswith(data):
            raise Exception(f"{rel_path} is not a valid path within the dataset.")
        return path
        
    @property
    def path(self, final=False):
        root_dir = "/nps/datasets/{}/{}/{}/{}/".format(self.id[0], self.id[1], self.id[2], self.id[3])
        final_path = os.path.join(root_dir, self.id)
        if os.path.exists(final_path) or final:
            return final_path
        else:
            temp_path = os.path.join(root_dir, "." + self.id)
            os.makedirs(temp_path, exist_ok=True)
            return temp_path
    
    def archive(self):
        memory_file = BytesIO()
        with zipfile.ZipFile(memory_file, 'w') as zf:
            data_path = os.path.join(self.path, 'data')
            for root, dirs, files in os.walk(data_path):
                for f in files:
                    full_path = os.path.join(root, f)
                    zf.write(full_path, os.path.relpath(full_path, data_path))
        memory_file.seek(0)
        return memory_file

@hug.exception(Exception)
def handle_exception(exception):
    return {
        'error': "An exception occured",
        'message': str(exception)
    }

@hug.get("/datasets/{dataset_id}.zip", output=hug.output_format.file, versions=2)
def download_dataset(dataset_id: hug.types.length(40, 41), response):
    d = Dataset(dataset_id)
    response.append_header('Content-Disposition', f'attachment; filename="{dataset_id}.zip"')
    return d.archive()

@hug.get("/datasets/{dataset_id}/data/{path}", output=hug.output_format.file, versions=2)
def download_dataset(dataset_id: hug.types.length(40, 41), path:hug.types.text, response):
    d = Dataset(dataset_id)
    path = d.get_path(path)
    return path

@hug.put("/datasets/{dataset_id}/data", versions=2)
def upload_file(dataset_id: hug.types.length(40, 41), body, response):
    d = Dataset(dataset_id)
    for filename, content in body.items():
        d.add_file(filename, content)
    return [d.id]

@hug.get("/datasets/{dataset_id}", versions=2)
def fetch_dataset_info(dataset_id: hug.types.length(40, 41)):
    d = Dataset(dataset_id)
    info = {
        "id": d.id,
        "path": d.path,
        "mutable": d.mutable
    }
    return info

@hug.put("/datasets/{dataset_id}", versions=2)
def set_dataset_info(dataset_id: hug.types.length(40, 41), mutable:hug.types.smart_boolean=True):
    d = Dataset(dataset_id)
    print(mutable)
    if not mutable:
        d.mutable = False
    return [d.id]

@hug.post("/datasets/", versions=2)
def upload_dataset(body, response):
    print(body)
    h = hashlib.sha1()
    for filename, content in body.items():
        h.update(content)
    d = Dataset(h.hexdigest().lower())
    for filename, content in body.items():
        d.add_file(filename, content)
    return [d.id]

