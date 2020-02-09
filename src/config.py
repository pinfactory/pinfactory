# This is used for testing in a container, at localhost:5000
# Should be overwritten for installing on a live server.

DB_NAME = 'market'
DB_USER = 'postgres'
DB_HOST = 'localhost'
DB_PORT = 5432

SECRET_KEY = 'localhost'
GITHUB_CLIENT_ID = "Iv1.025402c3c3c5e51c"
GITHUB_CLIENT_SECRET = "4424183d39afa4b5272cb9e114b99adbb46720e4"

GITHUB_WEBHOOK_SECRET = "xyzzy"

# Show the match button if the offer is your own.
MATCH_OWN_OFFERS = True
