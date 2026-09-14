#!/usr/bin/env bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
source /tmp/versions.env

apt-get update
apt-get install -y --no-install-recommends \
    postgresql-client mariadb-client redis-tools sqlite3 \
    libpq-dev default-libmysqlclient-dev unixodbc-dev

curl -fsSL https://pgp.mongodb.com/server-8.0.asc | gpg --dearmor -o /etc/apt/keyrings/mongodb.gpg
echo "deb [signed-by=/etc/apt/keyrings/mongodb.gpg] https://repo.mongodb.org/apt/ubuntu noble/mongodb-org/8.0 multiverse" > /etc/apt/sources.list.d/mongodb.list
apt-get update
apt-get install -y --no-install-recommends mongodb-mongosh mongodb-database-tools

curl -fsSL "https://github.com/xo/usql/releases/download/v${USQL_VERSION}/usql_static-${USQL_VERSION}-linux-amd64.tar.bz2" -o /tmp/usql.tbz2
tar -xjf /tmp/usql.tbz2 -C /usr/local/bin usql_static && mv /usr/local/bin/usql_static /usr/local/bin/usql && rm -f /tmp/usql.tbz2

rm -rf /var/lib/apt/lists/*