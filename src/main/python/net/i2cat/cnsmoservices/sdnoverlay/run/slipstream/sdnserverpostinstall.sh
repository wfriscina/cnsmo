#!/bin/bash

touch test0.out

echo -n "127.0.1.1 " >> /etc/hosts
hostname >> /etc/hosts

DIRECTORY='/var/tmp/slipstream'
if [ ! -d "$DIRECTORY" ]; then
  mkdir -p ${DIRECTORY}
fi
cd ${DIRECTORY}

file_done='/.post-install-done'
if [ ! -f $file_done ]; then
    
    if [ $(docker --version 1>/dev/null 2>/dev/null; echo $?) != "0" ] ; then
        echo "docker MUST BE installed"
        # install docker
        curl -fsSL https://get.docker.com/ | sh
        current_user=$(whoami)
        usermod -aG docker ${current_user}
    else
        echo "docker already installed"
    fi
    
    touch ${file_done}

    branch=ss-get --timeout=1200 net.i2cat.cnsmo.git.branch
    # Download the repositories from gitHub
    git clone -b $branch --single-branch https://github.com/dana-i2cat/cnsmo.git ./cnsmo
    git clone -b master --single-branch https://github.com/dana-i2cat/cnsmo-net-services.git ./cnsmo-net-services

    cwd=${PWD}
    python ${cwd}/cnsmo/cnsmo/src/main/python/net/i2cat/cnsmoservices/integrated/run/slipstream/netservicesserverpostinstall.py &
    disown $!
    ss-get --timeout=1200 net.services.installed # crear variable
    
fi