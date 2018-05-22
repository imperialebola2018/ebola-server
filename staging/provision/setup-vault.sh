#!/usr/bin/env bash
set -ex

if which -a vault > /dev/null; then
    echo "vault is already installed"
else
	echo "installing vault"
	sudo apt-get update
	sudo apt-get install -y unzip
	vault_zip=vault_0.7.3_linux_amd64.zip
	wget https://releases.hashicorp.com/vault/0.7.3/$vault_zip
	unzip $vault_zip
	chmod 755 vault
	sudo cp vault /usr/bin/vault
	rm -f $vault_zip vault
fi
