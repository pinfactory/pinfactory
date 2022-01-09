#!/bin/sh

# Start the database in the background
service postgresql start

# Run the command passed in from outside the container
exec $*
