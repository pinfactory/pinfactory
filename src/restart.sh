#!/bin/bash

set -e
set -x

# Run this script from inside its own directory
trap popd EXIT
pushd $PWD
cd $(dirname "$0")

# Application config file. (Overwrite the version used
# for testing in a container)
cp conf/config.py .

# Dependencies
apt-get update
apt-get -y install postgresql python3-pip apache2 libapache2-mod-wsgi-py3 libpq-dev
pip3 install -r requirements.txt

# Crontab entries
chown root.root conf/cron/*/*
chmod 755 conf/cron/*/*
cp -p conf/cron/daily/* /etc/cron.daily
cp -p conf/cron/weekly/* /etc/cron.weekly

# Apache web server (virtual host) configuration
cp conf/000-default.conf /etc/apache2/sites-available
cp conf/000-default-le-ssl.conf /etc/apache2/sites-available

# Config file for WSGI on the web server
cp conf/wsgi.conf /etc/apache2/conf-available
a2enmod wsgi
a2enconf wsgi

# Other needed Apache modules
a2enmod ssl
a2enmod rewrite

# Set up the database (same as in the container). Web
# server should be down when database is being worked on.
systemctl stop apache2
./db_setup.sh

# Finally restart the database and web servers
systemctl start postgresql
systemctl start apache2
