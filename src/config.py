# This is used for testing in a container, at localhost:5000
# Should be overwritten for installing on a live server.
from os import environ

DB_NAME = environ.get("DB_NAME", default="market")
DB_USER = environ.get("DB_USER", default="postgres")
DB_HOST = environ.get("DB_HOST", default="localhost")
DB_PORT = environ.get("DB_PORT", default="5432")
DB_PASSWORD = environ.get("DB_PASSWORD", default="")

SECRET_KEY = "localhost"

GITHUB_CLIENT_ID = "Iv23liEsuc2nx88BSlur"
GITHUB_CLIENT_SECRET = "9a30643ff1c0eab0c55d4b678503f016ce987e64"

# Show the match button if the offer is your own.
MATCH_OWN_OFFERS = True

DEBUG = True
ENV = "development"
