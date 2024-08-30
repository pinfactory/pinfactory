# This is used for testing in a container, at localhost:5000
# Should be overwritten for installing on a live server.
from os import environ

DB_NAME = environ.get("DB_NAME", default="market")
DB_USER = environ.get("DB_USER", default="postgres")
DB_HOST = environ.get("DB_HOST", default="localhost")
DB_PORT = environ.get("DB_PORT", default="5432")
DB_PASSWORD = environ.get("DB_PASSWORD", default="")

SECRET_KEY = "localhost"
GITHUB_CLIENT_ID = environ.get("GITHUB_CLIENT_ID", default="Iv1.025402c3c3c5e51c")
GITHUB_CLIENT_SECRET = environ.get(
    "GITHUB_CLIENT_SECRET", default="4424183d39afa4b5272cb9e114b99adbb46720e4"
)

GITHUB_WEBHOOK_SECRET = environ.get("GITHUB_WEBHOOK_SECRET", default="xyzzy")

# Show the match button if the offer is your own.
MATCH_OWN_OFFERS = True

DEBUG = True
ENV = 'development'
