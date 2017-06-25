#!/bin/bash
IMAGE_PREFIX="registry.docker.neuro.ukm.ms/nps/"
IMAGE_VERSION=$(git rev-parse --short --verify HEAD)

for component in components/*/
do
    component="${component%/}"     # strip trailing slash
    component="${component##*/}"   # strip path and leading slash
    IMAGE_NAME="${IMAGE_PREFIX}${component}:${IMAGE_VERSION}"
    echo ${IMAGE_NAME}
    docker build --tag "${IMAGE_NAME}" --tag "${component}:${IMAGE_VERSION}" components/${component}
    docker push "${IMAGE_NAME}"
done
