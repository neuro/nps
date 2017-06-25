#!/bin/bash
ROOT_DIR="/tmp/nps/test"
DATA_DIR="${ROOT_DIR}/datasets"
APP_DIR="${ROOT_DIR}/applications"
VERSION=$(git rev-parse --short --verify HEAD)
IMAGE="nps-runner:${VERSION}"

docker build --tag "${IMAGE}" .
docker run --rm -it -v ${DATA_DIR}:/nps/datasets  -v /var/run/docker.sock:/var/run/docker.sock --network nps-internal ${IMAGE}