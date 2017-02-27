#!/bin/sh -e

[[ -z "${DART_CONFIG}" ]] && echo "environment variable needs to be set: DART_CONFIG" && exit 1
source ../util.sh
source ./docker-local-init.sh

pushd ../../ > /dev/null

echo "reading configuration: ${DART_CONFIG}"
OLD_IFS=${IFS}
IFS=
CONFIG="$(DART_ROLE=tool dart_conf)"
POSTGRES_USER=$(dart_conf_value "${CONFIG}" "$.local_setup.postgres_user")
POSTGRES_PASSWORD=$(dart_conf_value "${CONFIG}" "$.local_setup.postgres_password")
POSTGRES_DOCKER_IMAGE=$(dart_conf_value "${CONFIG}" "$.local_setup.postgres_docker_image")
IFS=${OLD_IFS}

docker run --name dart-postgres -d -p 5432:5432 \
    -e POSTGRES_USER="${POSTGRES_USER}" \
    -e POSTGRES_PASSWORD="${POSTGRES_PASSWORD}" ${POSTGRES_DOCKER_IMAGE}


popd > /dev/null
