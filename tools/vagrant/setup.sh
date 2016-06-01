#!/usr/bin/env bash

set +x

# The epel-release has repos for other downloads.
# we get the tools needed to install dart locally.
sudo yum install epel-release -y
sudo yum install vim-enhanced mlocate git docker docker-registry python-pip python-wheel python-pip python-wheel postgresql-devel python-devel npm  -y

# Get the dart repo. We need the ssh keys (stored in the ./ssh_files) in order to clone.
HOME_DIR=/home/vagrant
PROJ_DIR=${HOME_DIR}/projects
echo $PROJ_DIR
   # placing ssh keys in root and /home/vagrant directories so we can git clone as both users
   sudo mkdir -p /root/.ssh &&
   sudo cp /vagrant_data/ssh_files/* /root/.ssh &&
   mkdir -p ${HOME_DIR}/.ssh &&
   cp /vagrant_data/ssh_files/* /${HOME_DIR}/.ssh &&
   # download the dart and dart-config repos to ~/projects
   mkdir -p /home/vagrant/projects && 
   cd /home/vagrant/projects && 
   git clone https://github.com/RetailMeNotSandbox/dart.git &&
   git clone ssh://git@stash.rmn.com:7999/data/dart-config.git  

# pip install requirements for the python project   
cd ${PROJ_DIR}/dart/src/python/ && sudo pip install --upgrade pip &&  sudo pip install -r requirements.txt

# install UI (e.g. angular) packages
# setup bower (used for dart UI)
sudo npm install bower -g && cd /home/vagrant/projects/dart/src/python/dart/web/ui && bower install

# Needed in order to use the docker provisioner
# we also move Dockerfiles to their own directories so they can be named Dockerfile and we can use the vagrant provisioner
sudo groupadd -f docker
mkdir -p /tmp/elasticmq && cp /home/vagrant/projects/dart/tools/docker/Dockerfile-elasticmq /tmp/elasticmq/Dockerfile
sudo updatedb # indexes all used files

# setup env variables:
# To make sure they will be set next time we login to a session
echo "export AWS_SECRET_ACCESS_KEY=value" > /home/vagrant/.bashrc &&
echo "export AWS_SECRET_ACCESS_KEY=value" >> /home/vagrant/.bashrc &&
echo "export DART_ROLE=web" >> /home/vagrant/.bashrc &&
echo "export DART_CONFIG=/home/vagrant/projects/dart-config/dart-local.yaml" >> /home/vagrant/.bashrc
echo "export PYTHONPATH=/home/vagrant/projects/dart/src/python" >> /home/vagrant/.bashrc

# preparing to run the webserver using the same env variables as above
export AWS_SECRET_ACCESS_KEY=1 && export AWS_SECRET_ACCESS_KEY=2 && export DART_ROLE=web && export DART_CONFIG=/home/vagrant/projects/dart-config/dart-local.yaml && export PYTHONPATH=/home/vagrant/projects/dart/src/python


### launch the web server
cd ${PROJ_DIR}/dart/src/python/dart/web && python  ./server.py
