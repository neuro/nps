#!/bin/bash
ROOT_DIR="/tmp/nps/test"
DATA_DIR="${ROOT_DIR}/datasets"
APP_DIR="${ROOT_DIR}/applications"
VERSION=$(git rev-parse --short --verify HEAD)
IMAGE="nps-metadata-writer:${VERSION}"

docker build --tag "${IMAGE}" .
docker run --rm -it -v ${DATA_DIR}:/datasets --network nps-internal ${IMAGE}