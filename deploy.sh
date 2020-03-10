#!/bin/bash

set -e
set -x

# Remove the temp copy of config file and return to the
# original directory on exit.
cleanup(){
	rm -f conf/config.py
	popd
}
trap 'cleanup' EXIT
pushd $PWD
cd $(dirname "$0")

HOST=market.pinfactory.org
USER=market
DOCROOT=/srv/market

EXCLUDES="--exclude include --exclude .git --exclude lib --exclude bin --exclude lib64 --exclude tmp"

ssh $USER@$HOST true
rm -rf data

scp $USER@$HOST:$DOCROOT/config.py conf/config.py || pass config/market > conf/config.py
ssh $USER@$HOST sudo apt-get -y install rsync
ssh $USER@$HOST sudo mkdir -p $DOCROOT
ssh $USER@$HOST sudo chown -R $USER $DOCROOT
rsync -rpt $EXCLUDES src/ $USER@$HOST:$DOCROOT/
rsync -rpt $EXCLUDES conf $USER@$HOST:$DOCROOT/
ssh $USER@$HOST sudo $DOCROOT/restart.sh
