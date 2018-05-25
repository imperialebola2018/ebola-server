#!/usr/bin/env bash
set -ex

if which -a vault > /dev/null; then
    echo "vault is already installed"
else
    echo "installing vault"
    sudo apt-get update
    sudo apt-get install -y unzip
    VAULT_VERSION=0.10.1
    VAULT_ZIP=vault_${VAULT_VERSION}_linux_amd64.zip
    wget https://releases.hashicorp.com/vault/${VAULT_VERSION}/${VAULT_ZIP}
    unzip $VAULT_ZIP
    chmod 755 vault
    sudo cp vault /usr/bin/vault
    rm -f $VAULT_ZIP vault
fi
