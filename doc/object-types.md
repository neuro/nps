# NPS Object Types
The basic NPS object types are Dataset, Mount, Job, and Pipeline. These objects are used to describe all actions and data in the system.

## Dataset
The most basic object in NPS is a Dataset, which is simply a bunch of files identified by an SHA1 hash. For DICOM imports the hash is computed on the `SeriesInstanceUID`. For Job results the hash is computed on the JSON description of the Job, see the help on the Job object type for detailed information on this. This allows the system to re-use results without actually running equivalent Jobs twice.

Datasets are stored in the system at `/nps/datasets/a/b/c/d/<hash>`. Where `a`, `b`, `c`, and `d` are the first four characters of the hash. Each dataset may contain a folder called `.nps` at the root level for metadata. The contents of this directory should generally be treated as opaque values. Basically same as `.git`.

### Example
```json
{
	"id": "29ce4b2c3185ec069830a4a3dfad582547f4bc3a"
}
```

## Mount
A Mount specifies a relationship between an existing resource and the container in which a job is executed. While the actual resource being mounted is always a Dataset, resources can also refer to user inputs or the result of previous Jobs. Note that not all `type` values are valid in every circumstance.

### Mount Attributes
| Attribte | Description | Required? | Possible Values |
| --- | --- | --- | --- |
| type | Type of the mounted resource | Yes | `dataset`, `user`, `step` |
| name | Identifier of the mounted resource | Yes | Depends on `type` |
| path | Mountpoint within the container | Yes | Valid absolute path |

### Examples

#### Mounting a Static Dataset
This is the most straightforward way of specifying a Mount and is always valid. The definition below mounts Dataset `29ce4b2c3185ec069830a4a3dfad582547f4bc3a` at `/input`.

```json
{
	"type": "dataset",
	"name": "29ce4b2c3185ec069830a4a3dfad582547f4bc3a",
	"path": "/input"
}
```

#### Mounting a User-Selected Dataset
This example asks the user to specify a Dataset ID named `t1` and mounts the Dataset with the given id at `/input`. Note that the actual way in which the user specifies the Dataset (e.g. a web interface or a command line argument) is undefined. This kind of Mount cannot be used in non-interactive environments where the user has no way to input additional data.

```json
{
	"type": "user",
	"name": "t1",
	"path": "/input"
}
```

#### Mounting a Previous Job's Result
This Mount type is only available as part of a Pipeline specification. The example given below waits for the step `convert-t1-to-nifti` to finish and mounts the resulting Dataset to `/input/t1`.

```json
{
    "type": "step",
    "name": "convert-t1-to-nifti",
    "path": "/input/t1"
}
```

## Job
Jobs should generally have a `name`, which does not need to be unique. `name` is required if the Job's output is referenced as part of a Pipeline. For a single Job only `dataset` mounts are supported.

### Job Attributes
| Attribute | Description | Required? |
| --------  | ----------- | --------- |
| name | Job name    | No        |
| force | Disallow cached results | No |
| image | Docker image to use, should include tag | Yes |
| command | Command to run in the docker image | Yes, may be empty |
| mounts | List of mounts to use when executing | Yes |

### Example
```json
{
    "name": "convert-to-nifti",
    "image": "janten/dcm2niix:v1.0",
    "command": "dcm2niix /input /output",
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

### Notes
The use of the `latest` tag in the `image` attribute is strongly discouraged and may be rejected by some versions of the system. This also applies to the implicit fallback to `latest` by not using a tag at all.

The `name` and `force` attributes are ignored when computing the SHA1 hash for the resulting Dataset. 

## Pipeline
A Pipeline is a set of related Jobs that are executed in a specified order. Pipelines have a required `name` and `description`.

### Inputs and Steps
Required and optional inputs to the Pipeline are specified in `inputs`. The only supported input type is `dataset` which needs a `name` for later reference. The `description` field is required and shown in user interfaces. It should give a short, succinct description of the value and its use in the pipeline. The `required` attribute specifies wether the input must be specified by the user and defaults to `true`. You must specify a `default` value if `required == false`, even if the actual value is not used in your Pipeline.

The `steps` array specifies the Jobs that are part of this pipeline. The Jobs will be ran in the specified order so you can only reference the results of earlier steps. A step definition is similar to a Job but supports additional values for the `type` attribute of its `mounts`:

* `user` mounts reference an input Dataset selected by the user by its `name` as specified in `inputs`.
* `step` mounts reference the output of an earlier step in the pipeline by its `name`.

### Executing a Pipeline
A Pipeline is just a template for a series of jobs. To convert a Pipeline and some given input values to a concrete array of Jobs in pseudocode:

1. Get the first step from the `steps` attribute
2. Convert the step to a Job by replacing all its placeholder `mounts` (i.e. `type != dataset`) with dataset mounts by changing their type to `dataset` and their `name` to the Dataset id obtained from user input or a previous Job invocation.
3. Schedule the created Job by submitting it to the NPS job queue. The Job will be enqueued any will generally not be started right away -- it may not be started at all if the system can use a cached result. The system will respond with a new Dataset ID. This is the ID of the resulting output Dataset of this job and should be used to fill the `type == step` placeholder mounts of upcoming steps.
4. Fetch the next step and continue at 2.

Your implementation may validate the whole Pipeline before beginning execution. Abort execution if you reach a step whose mounts cannot be constructed due to insufficient data from user input or previous steps. Jobs must always be enqueued in order. Don't manage dependencies between steps in your Job generation code.

### Pipeline Attributes
| Attribute | Description | Required? |
| --------  | ----------- | --------- |
| name | The pipeline name | Yes        |
| description | User-visible information about this pipeline | Yes |
| inputs | Required and optional Dataset references | Yes |
| steps | A list of job definitions to execute as part of the Pipeline | Yes |

### Example
```json
{
    "name": "FreeSurfer",
    "description": "Run FreeSurfer on T1 dataset",
    "inputs": [
        {
            "type": "dataset",
            "name": "t1",
            "description": "T1 DICOM dataset to work with",
            "required": true,
            "default": null
        },
        {
            "type": "dataset",
            "name": "t2",
            "description": "T2 weighted image for better pial reconstruction",
            "required": false,
            "default": null
        }
    ],
    "steps": [
        {
            "name": "convert-t1-to-nifti",
            "image": "janten/dcm2niix",
            "command": "dcm2niix /input /output",
            "mounts": [
                {
                    "type": "user",
                    "name": "t1",
                    "path": "/input"
                }
            ]
        },
        {
            "name": "convert-t2-to-nifti",
            "image": "janten/dcm2niix",
            "command": "dcm2niix /input /output",
            "mounts": [
                {
                    "type": "user",
                    "name": "t2",
                    "path": "/input"
                }
            ]
        },
        {
            "name": "run-freesurfer",
            "image": "neurology/freesurfer:5.6",
            "command": "recon-all --all",
            "mounts": [
                {
                    "type": "step",
                    "name": "convert-t1-to-nifti",
                    "path": "/input/t1"
                },
                {
                    "type": "step",
                    "name": "convert-t2-to-nifti",
                    "path": "/input/t2"
                }
            ]
        }
    ]
}
```
