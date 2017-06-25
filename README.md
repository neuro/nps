# Neuroimage Processing System

## File system structure

- Root is always (mounted at) `/nps`
- Imported and processed datasets are equal
 - Stored at `/nps/datasets`
 - Identified by an SHA1 hash `/nps/datasets/a/b/c/d/<hash>`. Where `a`, `b`, `c`, and `d` are the first four characters of the hash.
 - For imported datasets, the hash is `sha1(SeriesInstanceUID)`
 - For results: `sha1(job.json())`. This value may be dependent on the server environment because of differences in JSON formatting.
- Each dataset may contain a folder called `.nps` at the root level for metadata. The contents of this directory should generally be treated as opaque values. Basically same as `.git`.

## Jobs
- Jobs can be run locally or remotely. The output will be the same, `<hash>` may be different.
- A job consists of a docker image, a command and an optional set of input datasets mounted to the container.
 - Input datasets are always mounted read-only at a location specified by the user. This works basically the same way as docker mounted volumes. `-d <hash>:/input/t1` will mount the dataset identified by `<hash>` at location `/input/t1`.
- The system will provide a writeable output directory at `output`. This is the output dataset.
- Jobs can be run and submitted with the `nps` utility. The returned value is the `<hash>` of the result directory, which may not exists immediatly after submission.

```
$ nps
usage: nps <command> [<args>]

   run	   Perform work on a dataset locally
   submit  Enqueue a job on the servers

$ nps run -d 655a01a7ae5791e80813f6d185fec0cfa2943798:/input neurodebian:jessie sleep 10
cfe20086ccc39f37088cf48b7ce4f56ff4520dd7d7583036b1a571d2a8913d73
```

## API
The system consists of a set of loosely coupled subsystems. Jobs can be run locally on an air-gapped computer. There is a REST API for these tasks:

- Enqueueing and monitoring remote jobs.
- Adding metadata to a dataset.
- Accessing datasets over HTTP. This includes metadata and raw file access.
- Authenticating users.
- Running queries on the metadata.

### Example API Usage
These are tasks that should be possible to achieve within the system in a reasonable timeframe.

#### Defining Groups
1. Find a set of datasets by any combination of sequence, date, patient's name, etc.
2. Permanently group these datasets for later retrieval. The group must stay unchanged even if new data is added to the system.
3. Apply additional filtering to the members of this group, e.g. only get diffusion weighted datasets.

#### Data Analysis
4. Run a specified script an each dataset of a group or the result of an arbitrary query.
5. Provide access to the results of this script.
   - Find descendants of a given dataset.
   - Add relevant metadata obtained by the script to a searchable database.
6. Output a subset of the results accross all processed datasets in a machine-readable format.

#### Group Analysis
1. Run a _single_ script on _all_ datasets of a group or query. Example: Create a mean registration template by averaging all subjects.
