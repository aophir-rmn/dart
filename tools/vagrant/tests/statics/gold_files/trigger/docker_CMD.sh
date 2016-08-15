#!/bin/sh

set -x
set -e

pip install -r /tmp/src/python/requirements.txt



pushd /tmp/src/python/dart/worker
python ./trigger.py