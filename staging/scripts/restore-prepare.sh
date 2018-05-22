#!/usr/bin/env bash
export VAULT_ADDR='https://ebola2018.dide.ic.ac.uk:8200'
if [ "$VAULT_AUTH_GITHUB_TOKEN" = "" ]; then
    echo -n "Please provide your GitHub personal access token for the vault: "
    read -s token
    echo ""
    export VAULT_AUTH_GITHUB_TOKEN=${token}
fi
env | grep -E '^(VAULT_ADDR|VAULT_AUTH_GITHUB_TOKEN)' > shared/vault_config
