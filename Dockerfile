# Setting up needed packages and dependencies.

FROM jgoerzen/debian-base-security:bullseye
ENV TERM linux
RUN DEBIAN_FRONTEND=noninteractive apt-get update
RUN DEBIAN_FRONTEND=noninteractive apt-get -y install postgresql python3-pip libpq-dev sudo faketime
RUN DEBIAN_FRONTEND=noninteractive apt-get clean && rm -rf /var/lib/apt/lists/*

RUN mkdir /srv/market
COPY src/requirements.txt /srv/market
RUN pip3 install -r /srv/market/requirements.txt

# Copying live data from live site into Docker container.

COPY src/db_setup.sh /srv/market/
COPY src/pg_hba.conf /srv/market
COPY src/schema.sql /srv/market
RUN /srv/market/db_setup.sh
RUN service postgresql stop

ENTRYPOINT ["/bin/sh"]
