#!/usr/bin/env bash

set +x

# The epel-release has repos for other downloads.
# we get the tools needed to install dart locally.
sudo yum install epel-release -y
sudo yum install vim-enhanced git docker docker-registry python-pip python-wheel python-pip python-wheel postgresql-devel python-devel -y
sudo pip install --upgrade pip

# Get the dart repo. We need the ssh keys (stored in the ./ssh_files) in order to clone.
HOME_DIR=/home/vagrant
PROJ_DIR=${HOME_DIR}/projects
echo $PROJ_DIR
   sudo mkdir -p /root/.ssh && 
   sudo mkdir -p ${HOME_DIR}/.ssh && 
   sudo cp /vagrant_data/ssh_files/* /root/.ssh && 
   sudo cp /vagrant_data/ssh_files/* /${HOME_DIR}/.ssh && 
   sudo mkdir -p /home/vagrant/projects && 
   sudo chown -R vagrant:vagrant /home/vagrant/projects &&
   cd /home/vagrant/projects && 
   sudo git clone ssh://git@stash.rmn.com:7999/data/dart.git &&
   sudo chown -R vagrant:vagrant /home/vagrant/projects 

cd ${PROJ_DIR}/dart/src/python/ && sudo pip install -r requirements.txt

# Needed in order to use the docker provisioner
# we also move Dockerfiles to their own directories so they can be named Dockerfile and we can use the vagrant provisioner
sudo groupadd -f docker
mkdir -p /tmp/elasticmq && cp /home/vagrant/projects/dart/tools/docker/Dockerfile-elasticmq /tmp/elasticmq/Dockerfile

