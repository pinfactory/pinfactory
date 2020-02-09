#!/bin/bash

dockerfail() {
	echo
	echo "Docker not found. Check that Docker is installed and running."
	echo 'See the "Getting Started" section of README.md for more info.'
	echo
	exit 1
}

docker ps &> /dev/null || dockerfail

# list all images for which the market specific stuff has not been done.
BASES=$(for img in $(docker image ls -aq); do docker image history $img | grep -q '/srv/market' || echo $img; done)

# From that list, find the image that has had the Debian packages installed.
for b in $BASES; do
	if (docker history $b | grep -q "apt-get -y install"); then
		docker tag $b market-debian-base
		echo "Tagged base image $b"
		break
	fi
done

# Remove anything not tagged "debian"
echo -n "Cleaning up Docker images: "
docker image ls | grep -v debian | awk 'NR>1 {print $3}' | xargs docker rmi -f 2> /dev/null | grep "^Deleted" | wc -l

# prune all files that are now unused
docker system prune

echo
echo "Remaining Docker images"
docker image ls
