#!/bin/sh -e

[[ -z "${DART_CONFIG}" ]] && echo "environment variable needs to be set: DART_CONFIG" && exit 1
source ../util.sh
source ./docker-local-init.sh

pushd ../../ > /dev/null

echo "reading configuration: ${DART_CONFIG}"
OLD_IFS=${IFS}
IFS=
CONFIG="$(DART_ROLE=tool dart_conf)"
DOCKER_IMAGE_ELASTICMQ=$(dart_conf_value "${CONFIG}" "$.local_setup.elasticmq_docker_image")
IFS=${OLD_IFS}
$(aws ecr get-login)

docker run --name dart-elasticmq -d -p 9324:9324 ${DOCKER_IMAGE_ELASTICMQ}


popd > /dev/null
