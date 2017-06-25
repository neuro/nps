#!/bin/bash
docker build --tag dicom-indexer .
docker run -v /Users/janten/Downloads:/input:ro -v $(pwd):/output dicom-indexer