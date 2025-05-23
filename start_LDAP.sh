
#!/bin/bash
set -e

# Start LDAP server in docker container
sudo docker pull bitnami/openldap:latest
sudo docker compose -f .github/workflows/docker-configs/ldap-docker-compose.yml up -d
sudo docker ps
