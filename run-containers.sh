#!/bin/bash

# This shell script will build and run Dockerfile-pinfactory and Dockerfile-postgres
# and connect the frontend up with the postgresql running in the container.
# After running this script the features market should be available on localhost:8123

USER=markethandler
PASSWORD=test123
DBNAME=market

docker build -t pinfactory-test:latest -f Dockerfile-pinfactory-wsgi .
docker build -t pinfactory-postgres:latest -f Dockerfile-postgres .

if [ ! "$(docker ps -q -f name=pin-postgres)" ]; then
    if [ "$(docker ps -aq -f status=exited -f name=pin-postgres)" ]; then
        # cleanup
        docker rm pin-postgres
    fi
    docker run \
    --rm \
    -d \
    -e POSTGRES_PASSWORD=$PASSWORD \
    -e POSTGRES_DB=$DBNAME \
    -e POSTGRES_USER=$USER \
    --name pin-postgres \
    --network host \
    pinfactory-postgres
fi

docker run \
    --rm \
	--network host \
    -e FLASK_ENV=development \
	-e LC_ALL=C.UTF-8 \
	-e LANG=C.UTF-8 \
    -e DBNAME=$DBNAME \
    -e PGUSER=$USER \
    -e PGHOST=0.0.0.0 \
    -e PGPORT=5432 \
    -e PGPASSWORD=$PASSWORD \
    -e PORT=8123 \
    --name pinfactory-test \
    pinfactory-test

docker stop pin-postgres
