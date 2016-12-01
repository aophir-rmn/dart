#!/usr/bin/env bash

sudo yum update -y

IMPALA_INSTALL_FILE=${1}
IMPALA_DOCKER_REPO_BASE_URL=${2}
IMPALA_VERSION=${3}

aws s3 cp ${IMPALA_INSTALL_FILE} .
chmod +x install_impala.rb
./install_impala.rb --docker-repo-base-url ${IMPALA_DOCKER_REPO_BASE_URL} --version ${IMPALA_VERSION} &
