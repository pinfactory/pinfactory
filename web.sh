#!/bin/bash

# This shell script is called at the prompt when starting the application demo from the 
# command line. This script uses Docker which is pertinent for running from a
# personal computer. The platform running on market.pinfactory.org is started with
# deploy.sh and restart.sh, as it does not use a Docker container (it uses up
# the entire server -- don't need an extra layer of Docker there).

#Datasource: where to ssh to get our data? Ensure we are in the same directory
#where the script lives.
DATASOURCE=market@market.pinfactory.org

trap popd EXIT
pushd $PWD &> /dev/null
cd $(dirname "$0")

#Reminder: start up Docker before running this. Docker makes it easier to setup
#dependencies and other systems regardless of OS (Mac, Windows, Linux). Postgres
#database will live within the Docker environment.
dockerfail() {
	echo
	echo "Docker not found. Check that Docker is installed and running."
	echo 'See the "Getting Started" section of README.md for more info.'
	echo
	exit 1
}
docker ps &> /dev/null || dockerfail
ssh $DATASOURCE true || echo "Can't connect to $DATASOURCE"

mkdir -p data
ssh $DATASOURCE pg_dump --user postgres market > data/db_dump.sql || echo "Failed to get live data from $DATASOURCE"

set -e
set -x

#Build a docker image using the files in the current directory. Makes it possible
#to have 2 installs in 2 different directories with suitable modifications to the
#port number and the tag market_web.
docker build --tag=market_web .

#We are setting the environment variable in Flask to specify that webapp.py is
#the application we want to run. Running happens in the last line below.
docker run \
	-p 5000:5000 \
	-e FLASK_APP=/srv/market/webapp.py \
	-e FLASK_ENV=development \
	-e LC_ALL=C.UTF-8 \
	-e LANG=C.UTF-8 \
	--volume "$(pwd)"/src:/srv/market:ro,Z \
	--entrypoint="/usr/local/bin/flask" market_web run --host=0.0.0.0
