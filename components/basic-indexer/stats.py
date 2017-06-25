import json, os, stat
from datetime import datetime
from glob import glob

def get_tree_size(path):
    """Return total size of files in given path and subdirs."""
    total = 0
    count = 0
    for entry in os.scandir(path):
        if entry.is_dir(follow_symlinks=False):
            t, c = get_tree_size(entry.path)
            total += t
            count += c
        else:
            total += entry.stat(follow_symlinks=False).st_size
            count += 1
    return (total, count)

info = {}
stats = os.stat("/input")
info["last_access"] = datetime.fromtimestamp(stats.st_atime).isoformat()
info["last_modification"] = datetime.fromtimestamp(stats.st_mtime).isoformat()
info["last_meta_change"] = datetime.fromtimestamp(stats.st_ctime).isoformat()
total, count = get_tree_size("/input")
info["size_bytes"] = total
info["files"] = count
        
with open("/output/fs_stats.json", "w") as file:
    json.dump(info, file, indent=4, sort_keys=True)
