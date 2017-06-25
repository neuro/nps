# NPS Runner
The runner connects to a Redis server at `nps-redis`, port 6379 and reads JSON encoded jobs from the queues `metadata-jobs` and `dataset-jobs`. Only jobs of version 2 are supported by this runner. Templates for the the kinds of supported jobs are given below. Each job type is only supported on the respective queue.

## Metadata Jobs
A metadata job adds new metadata to an existing dataset. These are rarely scheduled explicitly.

```
{
  "version": 2,
  "image": "alpine:latest",
  "command": "touch /output/seen"
  "dataset": "000af99b22aadb28f83413f92f2a19657c83fa71",
  "collection": "aaaaaaaaaaaaaaaa",
}
```

## Dataset Jobs
These are the main jobs in NPS that can mount an arbitrary number of datasets as inputs and create a new dataset as output.

```
{
  "version": 2,
  "image": "alpine:latest",
  "command": "touch /output/seen",
  "force": true,
  "mounts": [
      {
          "type": "dataset",
          "name": "29ce4b2c3185ec069830a4a3dfad582547f4bc3a",
          "path": "/input"
      }
  ]
}
```