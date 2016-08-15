#!/bin/sh

set -x
set -e

pip install -r /tmp/src/python/requirements.txt


npm install bower -g

cd /tmp/src/python/dart/web/ui && bower install --allow-root


pushd /tmp/src/python/dart/web
python ./server.py