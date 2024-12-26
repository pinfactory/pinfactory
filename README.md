# Pinfactory

A futures market for trading on the status of software
bugs and issues.


## Setup

This project has three prerequisites on the development
system: bash, curl, and Docker (or a Docker-compatible
container system).   See "Getting started".


## Design

This project has two priorities: correctness and testability.

 * we use a database schema that makes it as easy
   as possible to express market operations as simple
   queries.

 * we use constraints and triggers at the database level
   to avoid putting the market into a hard-to-understand
   state even in the event of an application bug

 * we put a simple object-oriented layer on top of the
   database, with methods to expose what is happening

 * this all makes it possible to write test code in natural
   language, to make it straightforward to translate
   use cases and user stories into tests.

 * Database transactions are market transactions.  The whole
   transaction should fail if there is a database inconsistency
   or error.


## Research funding

This software is an open source
implementation of a market design research
project described in [A market for trading software
issues](https://academic.oup.com/cybersecurity/article/5/1/tyz011/5580665).
This work has been funded by the Alfred
P. Sloan Foundation Digital Technology grant
on Open Source Health and Sustainability
(https://sloan.org/grant-detail/8434). Funding for
open access publishing of the paper was provided
by the University of Nebraska at Omaha Libraries'
Open Access Fund.


## Prices and quantities

All prices are expressed as the price of the
fixed side.  In the UI prices will be displayed
in the range 0 to 1, which translates nicely into
"the market believes that the probability of this bug
getting fixed is P." Internally prices are stored as
integers, 0 to 1000.

Internally, account balances are stored as millitokens
(1000x the amount shown in the UI).

Offer and contract quantities (in the "offer"
and "position" tables) are stored as numbers of
units. One unit represents a payout of one token
(1000 millitokens) to the winning side when the
contract is resolved.

The position table uses negative numbers for UNFIXED
positions, positive numbers for FIXED.  There are no
zero positions.


## Getting started

### On Linux

Install Docker (or a compatible container tool that provides the
`docker` command) from the package
manager and start it with the service manager.  Check your
distribution's instructions.

Test that you can connect with:

```
docker ps
```

If you get an error, you may need to add yourself to
the `docker` group and restart Docker.

```
sudo groupadd docker && sudo gpasswd -a ${USER} docker && sudo systemctl restart docker
newgrp docker
```


### On Mac OS

[Install Docker Desktop for
Mac](https://docs.docker.com/docker-for-mac/install/).
(You do not need to make a Docker Hub account, just
start Docker.)


## run tests

Run the tests in a container.

	./test.sh

(Docker must be running and you must be able to connect to it.)


## Use the web application in a demo environment

This script will attempt to copy data from the live
site, then start a local copy in a container.

	./web.sh

Visit the site at: http://localhost:5000/

Your changes in the `src` directory will show up in
the container, and Flask is configured to auto-reload
when you modify anything.


## Clean up Docker containers and images

This script is only for development systems where you
aren't using Docker for other things.  **Don't run
this script on a production system.**

    ./cleanup.sh

It keeps the base Debian images and images with extra
system packages installed (because these images take
a while to build and don't change often) and removes
all the other images.


## Modify Pinfactory code

[The New and Improved Flask Mega-Tutorial, by Miguel
Grinberg](https://courses.miguelgrinberg.com/p/flask-mega-tutorial)
covers all the background material you will need to know. We
encourage pull requests that are still at the "work in progress"
stage, and will help you get them ready to merge.


# Dependencies

**Bootstrap:** Widely used web front-end component library.

**PostgreSQL:** Widely used RDBMS.

**Python 3:** Language runtime.

**Python packages**

 * Altair: Graphing.

 * psycopg2: Widely used adapter for PostgreSQL.

 * flask: Full-featured but relatively simple web development framework.

 * flask-bootstrap: Package to integrate Bootstrap with Flask templates.

 * flask-wtf: Flask support for WTForms

 * loginpass: Wrapper for OAuth, with support for GitHub.

 * WTForms: Form building and validation package with CSRF protection

**Vega: front end visualizations**


# Third parties

**GitHub:** Used for login and issue tracking integration.

FIXME: CDNs for Bootstrap and Vega resources?


# References

[Altair: Declarative Visualization in Python](https://altair-viz.github.io/)

[Bootstrap](https://getbootstrap.com/)

[Flask, A Python Microframework](http://flask.pocoo.org/)

[The Flask
Mega-Tutorial](https://courses.miguelgrinberg.com/p/flask-mega-tutorial)

[Getting started with Docker (on Fedora Linux)](https://developer.fedoraproject.org/tools/docker/docker-installation.html)

[Link, G.J.P., Rao, M., Marti, D. et al. Marktplatz zur Koordinierung und Finanzierung von Open Source Software. HMD 56, 419–437 (2019). https://doi.org/10.1365/s40702-018-00474-6](https://doi.org/10.1365/s40702-018-00474-6)

[Malvika Rao, Georg J P Link, Don Marti, Andy Leak, Rich Bodo, A market for trading software issues, Journal of Cybersecurity, Volume 5, Issue 1, 2019, tyz011, https://doi.org/10.1093/cybsec/tyz011](https://doi.org/10.1093/cybsec/tyz011)

[psycopg2](https://pypi.org/project/psycopg2/)

[PostgreSQL: Documentation](https://www.postgresql.org/docs/)

[Vega – A Visualization Grammar](https://vega.github.io/vega/)

[WTForms Documentation](https://wtforms.readthedocs.io/en/stable/index.html)


[modeline]: # ( vim: set fenc=utf-8 spell spl=en autoindent textwidth=72 tabstop=4 shiftwidth=4 expandtab softtabstop=4: )

