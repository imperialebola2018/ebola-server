#!/usr/bin/env bash
set -e
NAME=$1
if [ ! "$#" -eq 1 ]; then
    echo "Expected one argument"
    exit 1
fi

hostname $NAME
sed -i "s/vagrant/$NAME/g" /etc/hosts
sed -i "s/vagrant/$NAME/g" /etc/hostname

cp /vagrant/bash_prompt /etc/bash_prompt
if grep bash_prompt /etc/bash.bashrc; then
    echo "Prompt already set up"
else
    echo ". /etc/bash_prompt" >> /etc/bash.bashrc
    echo "set_prompt" >> /etc/skel/.bashrc
    cp /etc/skel/.bashrc ~vagrant
    cp /etc/skel/.bashrc ~root
fi
