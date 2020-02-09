#!/bin/bash

# To jump time forward, run this script with the
# number of days to jump.
# For example, to jump 2 weeks:
#
#    ./timejump.sh 14
#
# This script takes a few seconds because the
# database must shut down and then restart with
# the fake time. Think of something to say during
# this time to make the demo flow better.

set -e

HOST=localhost:5000

curl -s http://$HOST/timejump?days=$1
echo
