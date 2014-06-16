import logging

from flask import Flask
from flask.ext.assets import Environment
from granoclient import Grano, NotFound

from connectedafrica import default_settings


logging.basicConfig(level=logging.DEBUG)

requests_log = logging.getLogger("requests")
requests_log.setLevel(logging.WARNING)

app = Flask(__name__)
app.config.from_object(default_settings)
app.config.from_envvar('COAF_SETTINGS', silent=True)

assets = Environment(app)


# Set up an API client for the grano instance:

client = Grano(api_host=app.config.get('GRANO_HOST'),
               api_key=app.config.get('GRANO_APIKEY'))
project_name = app.config.get('GRANO_PROJECT')

try:
    grano = client.get(project_name)
except NotFound:
    data = {'slug': project_name, 'label': project_name}
    #grano = client.projects.create(data)
    grano = None
