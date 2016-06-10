#!/usr/bin/env bash

set +x

# The epel-release has repos for other downloads.
# we get the tools needed to install dart locally.
sudo yum install epel-release -y
sudo yum install vim-enhanced mlocate python-pip python-wheel python-pip python-wheel postgresql-devel wget mc -y

# install docker-engine
sudo sh -c "wget -qO- https://get.docker.com/ | sh"

# we need to logout of the VM for thiese group changes to take effect. We will continue later with the additional_steps.sh  bash script.
sudo groupadd -f docker && sudo usermod -aG docker $USER
sudo updatedb # indexes all used files

# This script will be manually run to install docker-compose after logging in and out of the VM
# verify the group is docker by running "id" bash command: groups=1000(vagrant)
cp /vagrant_data/vagrant_scripts/additional_steps.sh ~ && chmod 755 ~/additional_steps.sh 

# needed for connecting containers:
sudo systemctl stop firewalld
sudo systemctl restart docker

# adding a shortcut for docker-compose
alias dc='docker-compose'
echo "alias dc='docker-compose'" > ~/.bashrc 
echo "alias dc='docker-compose'" > ~/.bash_profile
