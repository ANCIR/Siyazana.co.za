from flask import Flask, url_for
from flask_assets import Environment
from flask_cache import Cache
from flask_flatpages import FlatPages
from granoclient import Grano, NotFound

from connectedafrica import default_settings
from connectedafrica import logs # noqa

app = Flask(__name__)
app.config.from_object(default_settings)
app.config.from_envvar('COAF_SETTINGS', silent=True)

assets = Environment(app)
pages = FlatPages(app)
cache = Cache()
cache.init_app(app)

# Set up an API client for the grano instance:

client = Grano(api_host=app.config.get('GRANO_HOST'),
               api_key=app.config.get('GRANO_APIKEY'))
project_name = app.config.get('GRANO_PROJECT')

try:
    grano = client.get(project_name)
except NotFound:
    raise RuntimeError("Please run 'make loadschema' first!")


class SchemaCache(object):

    def __init__(self):
        self.cache = {}
        query = grano.schemata.query(params={'limit': 1000, 'full': 1})
        for schema in query.results:
            self.cache[schema.name] = schema

    def by_name(self, name):
        return self.cache.get(name)

    def by_obj(self, obj):
        named = {}
        for schema in self.cache.values():
            if schema.obj == obj:
                named[schema.name] = schema
        return named

    def schema(self, obj):
        for name, schema in self.cache.items():
            if name == obj.schema.name:
                return schema

    def attributes(self, obj):
        attribs = {}
        for attr in self.schema(obj).attributes:
            name = attr.get('name')
            attribs[name] = attr
        return attribs

schemata = SchemaCache()
