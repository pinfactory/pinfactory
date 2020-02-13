#!/bin/bash

# Start multiple Firefox browsers with different profiles
# for a web demo.

# Always run this script from its own directory
trap popd EXIT
pushd $PWD &> /dev/null
cd $(dirname "$0")

fail() {
        echo $*
        exit 1
}

# Find Firefox on Mac OS or Linux
if [ -e /Applications/Firefox.app/Contents/MacOS/firefox ]; then
	FIREFOX=/Applications/Firefox.app/Contents/MacOS/firefox
else
	FIREFOX=$(which firefox)
fi

# Check that Firefox and Docker are available
$FIREFOX -version || fail "Firefox not installed, not executable, or not on your path."
docker ps &> /dev/null || fail "Docker not installed or not running."

# Pre-build the container so it's cached.
docker build --tag=market_web .

# Make two new Firefox profiles for users Adam and Beth
# profiletmpdir=`mktemp -d 2>/dev/null || mktemp -d -t 'profiletmpdir'`
$FIREFOX -no-remote -CreateProfile "Adam" # $profiletmpdir/Adam"
$FIREFOX -no-remote -CreateProfile "Beth" # $profiletmpdir/Beth"
$FIREFOX -no-remote -CreateProfile "Charles" # $profiletmpdir/Charles"

# Start the browsers
(cd /tmp && sleep 8 && nohup $FIREFOX -no-remote -P Adam http://localhost:5000/localuser?name=Adam &) > /dev/null
(cd /tmp && sleep 8 && nohup $FIREFOX -no-remote -P Beth http://localhost:5000/localuser?name=Beth &) > /dev/null
(cd /tmp && sleep 8 && nohup $FIREFOX -no-remote -P Charles http://localhost:5000/localuser?name=Charles &) > /dev/null

# Run the local web site in a container
exec ./web.sh
