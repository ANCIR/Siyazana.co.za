
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


class SchemaCache(object):

    def __init__(self):
        self.cache = {}
        query = grano.schemata.query(params={'limit': 1000, 'full': 1})
        for schema in query.results:
            self.cache[schema.name] = schema

    def by_name(self, name):
        return self.cache.get(name)

    def by_obj(self, obj):
        for schema in self.cache.values():
            if schema.obj == obj:
                yield schema

    def schemata(self, obj):
        schemata = obj._data.get('schemata', [])
        if 'schema' in obj._data:
            schemata = [obj._data.get('schema')]
        schemata = [s['name'] for s in schemata]
        for name, schema in self.cache.items():
            if name in schemata:
                yield schema

    def attributes(self, obj):
        attribs = {}
        for schema in self.schemata(obj):
            for attr in schema.attributes:
                name = attr.get('name')
                attribs[name] = attr
        return attribs

schemata = SchemaCache()
