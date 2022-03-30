# Using Waitress as the WSGI server. https://docs.pylonsproject.org/projects/waitress/en/latest/
from email.policy import default
from waitress import serve
from webapp import app
from os import environ

serve(app, host='0.0.0.0', port=environ.get('PORT', default="80"))
