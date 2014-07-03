
from flask import Flask, url_for
from flask.ext.assets import Environment
from flask_flatpages import FlatPages
from granoclient import Grano, NotFound

from connectedafrica import default_settings
from connectedafrica import logs

app = Flask(__name__)
app.config.from_object(default_settings)
app.config.from_envvar('COAF_SETTINGS', silent=True)

assets = Environment(app)
pages = FlatPages(app)


# Set up an API client for the grano instance:

client = Grano(api_host=app.config.get('GRANO_HOST'),
               api_key=app.config.get('GRANO_APIKEY'))
project_name = app.config.get('GRANO_PROJECT')

try:
    grano = client.get(project_name)
except NotFound:
    data = {'slug': project_name, 'label': project_name}
    grano = client.projects.create(data)
