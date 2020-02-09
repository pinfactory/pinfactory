#!/bin/bash

set -e
set -x

trap popd EXIT
pushd $PWD
cd $(dirname "$0")

cp pg_hba.conf /etc/postgresql/9.6/main
service postgresql restart

# create the market database if it does not exist already
echo "SELECT 'CREATE DATABASE market' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'market')\gexec" | psql --user postgres

[ -e db_dump.sql ] && psql --user postgres market < db_dump.sql
psql --user postgres -d market -f schema.sql

