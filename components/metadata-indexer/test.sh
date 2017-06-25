#!/bin/bash
ROOT_DIR="/tmp/nps/test"
DATA_DIR="${ROOT_DIR}/datasets"
APP_DIR="${ROOT_DIR}/applications"
VERSION=$(git rev-parse --short --verify HEAD)
IMAGE="nps-metadata-indexer:${VERSION}"

mkdir -p "${APP_DIR}/metadata/index"
docker build --tag "${IMAGE}" .
docker run --rm -it -v ${DATA_DIR}:/datasets -v ${APP_DIR}/metadata:/metadata --network nps-internal ${IMAGE}