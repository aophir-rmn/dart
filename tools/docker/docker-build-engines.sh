#!/bin/sh -e

[[ -z "${DART_CONFIG}" ]] && echo "environment variable needs to be set: DART_CONFIG" && exit 1
source ../util.sh
source ./docker-local-init.sh

pushd ../../ > /dev/null


echo "reading configuration: ${DART_CONFIG}"
OLD_IFS=${IFS}
IFS=
CONFIG="$(DART_ROLE=tool dart_conf)"
DOCKER_IMAGE_ENGINE_NO_OP=$(dart_conf_value "${CONFIG}" "$.engines.no_op_engine.docker_image")
DOCKER_IMAGE_ENGINE_EMR=$(dart_conf_value "${CONFIG}" "$.engines.emr_engine.docker_image")
DOCKER_IMAGE_ENGINE_DYNAMODB=$(dart_conf_value "${CONFIG}" "$.engines.dynamodb_engine.docker_image")
DOCKER_IMAGE_ENGINE_REDSHIFT=$(dart_conf_value "${CONFIG}" "$.engines.redshift_engine.docker_image")
DOCKER_IMAGE_ENGINE_S3=$(dart_conf_value "${CONFIG}" "$.engines.s3_engine.docker_image")
DOCKER_IMAGE_ENGINE_ELASTICSEARCH=$(dart_conf_value "${CONFIG}" "$.engines.elasticsearch_engine.docker_image")
IFS=${OLD_IFS}

set -x
#docker build -f tools/docker/Dockerfile-engine-no_op         -t ${DOCKER_IMAGE_ENGINE_NO_OP} .
#docker build -f tools/docker/Dockerfile-engine-emr           -t ${DOCKER_IMAGE_ENGINE_EMR} .
#docker build -f tools/docker/Dockerfile-engine-dynamodb      -t ${DOCKER_IMAGE_ENGINE_DYNAMODB} .
#docker build -f tools/docker/Dockerfile-engine-redshift      -t ${DOCKER_IMAGE_ENGINE_REDSHIFT} .
#docker build -f tools/docker/Dockerfile-engine-s3            -t ${DOCKER_IMAGE_ENGINE_S3} .
docker build -f tools/docker/Dockerfile-engine-elasticsearch -t ${DOCKER_IMAGE_ENGINE_ELASTICSEARCH} .
set +x

REMOVABLE=$(docker images -f "dangling=true" -q)
[[ -n "${REMOVABLE}" ]] && docker rmi ${REMOVABLE}


popd > /dev/null
