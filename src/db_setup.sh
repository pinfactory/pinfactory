#!/bin/bash

set -e
set -x

trap popd EXIT
pushd $PWD
cd $(dirname "$0")

for pg_version in $(ls /etc/postgresql);
do
	cp pg_hba.conf /etc/postgresql/$pg_version/main
done
service postgresql restart

# create the market database if it does not exist already
echo "SELECT 'CREATE DATABASE market' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'market')\gexec" | psql --user postgres

[ -e db_dump.sql ] && psql --user postgres market < db_dump.sql
psql --user postgres -d market -f schema.sql
service postgresql stop
