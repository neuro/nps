#!/bin/bash
ROOT_DIR="/nps"
DATA_DIR="${ROOT_DIR}/datasets"
APP_DIR="${ROOT_DIR}/applications"
VERSION="$1"
IMAGE_PREFIX="registry.docker.neuro.ukm.ms/nps/"

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <version>"
    exit 1
fi

echo "Creating test environment at ${ROOT_DIR}"
mkdir -p "${DATA_DIR}" "${APP_DIR}"

echo "Switching to Docker swarm mode"
docker info | grep "Swarm: active" > /dev/null
if [ $? != 0 ]
then
    docker swarm init > /dev/null
else
    echo "Already in swarm mode"
fi

echo "Trying to create the internal overlay network"
docker network ls | grep "nps-internal" > /dev/null
if [ $? != 0 ]
then
    docker network create --driver overlay --attachable nps-internal >/dev/null 2>&1
else
    echo "Network exists"
fi

echo "(Re-)starting DICOM receiver"
docker service rm nps-dicom-receiver >/dev/null 2>&1
docker service create \
    --name nps-dicom-receiver \
    --network nps-internal \
    --replicas 1 \
    --mount type=bind,source=${DATA_DIR},destination=/datasets \
    -p 104:1040 \
    ${IMAGE_PREFIX}dicom-receiver:${VERSION}
echo "Receiver should be available at localhost:104"

REDIS_DIR="${APP_DIR}/redis/data"
echo "(Re-)starting Redis instance. Persisting data to ${REDIS_DIR}"
mkdir -p "${REDIS_DIR}"
docker service rm nps-redis >/dev/null 2>&1
docker service create \
    --name nps-redis \
    --network nps-internal \
    --mount type=bind,source=${REDIS_DIR},destination=/data \
    redis:3-alpine \
    redis-server --appendonly yes

echo "Installing built-in metadata generators and types"
cp -r ./environment/applications/metadata "${APP_DIR}/"

echo "Starting metadata writer, scheduler, scanner, and indexer"
META_DIR="${APP_DIR}/metadata"
mkdir -p "${META_DIR}" "${META_DIR}/index" "${META_DIR}/definitions"
docker service rm nps-metadata-indexer nps-metadata-writer nps-metadata-scheduler nps-metadata-scanner >/dev/null 2>/dev/null
docker service create \
    --name nps-metadata-indexer \
    --network nps-internal \
    --network internal \
    --mount type=bind,source=${DATA_DIR},destination=/datasets,readonly \
    --mount type=bind,source=${META_DIR},destination=/metadata \
    ${IMAGE_PREFIX}metadata-indexer:${VERSION}
docker service create \
    --name nps-metadata-writer \
    --network nps-internal \
    --mount type=bind,source=${DATA_DIR},destination=/datasets \
    ${IMAGE_PREFIX}metadata-writer:${VERSION}
docker service create \
    --name nps-metadata-scheduler \
    --network nps-internal \
    --mount type=bind,source=${META_DIR}/definitions,destination=/definitions,readonly \
    --mount type=bind,source=${DATA_DIR},destination=/datasets,readonly \
    ${IMAGE_PREFIX}metadata-scheduler:${VERSION}
docker service create \
    --name nps-metadata-scanner \
    --network nps-internal \
    --mount type=bind,source=${META_DIR}/definitions,destination=/definitions,readonly \
    --mount type=bind,source=${DATA_DIR},destination=/datasets,readonly \
    ${IMAGE_PREFIX}metadata-scanner:${VERSION}

echo "Starting NPS runner"
docker service rm nps-runner
docker service create \
    --name nps-runner \
    --network nps-internal \
    --mount type=bind,source=${DATA_DIR},destination=/nps/datasets \
    --mount type=bind,source=/var/run/docker.sock,destination=/var/run/docker.sock \
    ${IMAGE_PREFIX}runner:${VERSION}

echo "Starting API"
docker service rm nps-web-api
docker service create \
    --name nps-web-api \
    --network internal \
    --env "EXTERNAL_SUBDOMAIN=api.nps" \
    --mount type=bind,source=${DATA_DIR},destination=/nps/datasets \
    ${IMAGE_PREFIX}web-api:${VERSION}

echo "Send DICOM data to localhost:104 and watch your environment grow at ${ROOT_DIR}"