#!/bin/bash

trap popd EXIT
pushd $PWD &> /dev/null
cd $(dirname "$0")

dockerfail() {
	echo
	echo "Docker not found. Check that Docker is installed and running."
	echo 'See the "Getting Started" section of README.md for more info.'
	echo
	exit 1
}
docker ps &> /dev/null || dockerfail

set -e
set -x

docker build --tag=market_test .
docker run --volume "$(pwd)"/src:/srv/market:ro,Z \
	--entrypoint "/usr/bin/env" market_test python3 /srv/market/test.py

