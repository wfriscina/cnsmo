#!/usr/bin/env bash

if [ $(docker --version 1>/dev/null 2>/dev/null; echo $?) != "0" ] ; then
    # install docker
    curl -fsSL https://get.docker.com/ | sh
    current_user=$(whoami)
    usermod -aG docker ${current_user}
else
    echo "docker already installed"
fi

# download cnsmo
mkdir cnsmo
cd cnsmo
git clone --single-branch https://github.com/dana-i2cat/cnsmo.git
git clone --single-branch https://github.com/dana-i2cat/cnsmo-net-services.git
cd ..

# install cnsmo requirements
pip install -r cnsmo/cnsmo/requirements.txt

#install redis
wget http://download.redis.io/releases/redis-3.0.7.tar.gz
tar xzf redis-3.0.7.tar.gz
rm redis-3.0.7.tar.gz
cd redis-3.0.7
make
make install --quiet
cd ..