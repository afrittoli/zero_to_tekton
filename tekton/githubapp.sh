#!/bin/bash

# Simple script that runs indefinitely
# Creates a GitHub APP JWT from the private key
# Obtains an installation token with it
# Stores the token a secret in kubernets

JWT_TOKEN=$(ruby tekton/jwt.rb)
INSTALLATION_ID=$(curl -s -X GET -H "Authorization: Bearer $JWT_TOKEN" -H "Accept: application/vnd.github.v3+json" https://api.github.com/app/installations | jq .[0].id)
GITHUB_TOKEN=$(curl -s -X POST -H "Authorization: Bearer $JWT_TOKEN" -H "Accept: application/vnd.github.v3+json" https://api.github.com/app/installations/${INSTALLATION_ID}/access_tokens | jq -r .token)
kubectl delete secret github &> /dev/null || true
kubectl create secret generic github --from-literal=token=$GITHUB_TOKEN &> /dev/null || true

while true; do
    JWT_TOKEN=$(ruby tekton/jwt.rb)
    INSTALLATION_ID=$(curl -s -X GET -H "Authorization: Bearer $JWT_TOKEN" -H "Accept: application/vnd.github.v3+json" https://api.github.com/app/installations | jq .[0].id)
    GITHUB_TOKEN=$(curl -s -X POST -H "Authorization: Bearer $JWT_TOKEN" -H "Accept: application/vnd.github.v3+json" https://api.github.com/app/installations/${INSTALLATION_ID}/access_tokens | jq -r .token)
    date 2&>1 >> tekton/token.log
    kubectl patch secret github -p '{"data": {"token": "'$(printf ${GITHUB_TOKEN} | base64)'"}}' 2>&1 >> tekton/token.log
    sleep 240
done