from datetime import datetime, date
from urlparse import urlparse

from granoclient import Entity

from connectedafrica.core import app
from connectedafrica.views.base import blueprint as base_blueprint
from connectedafrica.views.browser import blueprint as browser_blueprint
from connectedafrica.views.profile import blueprint as profile_blueprint
from connectedafrica.views.profile import display_name
from connectedafrica import util
from connectedafrica.util.relations import relation_key_prop


app.register_blueprint(base_blueprint)
app.register_blueprint(browser_blueprint)
app.register_blueprint(profile_blueprint)


@app.context_processor
def inject_globals():
    return {
        'APP_NAME': app.config.get('APP_NAME'),
        'query_add': util.query_add,
        'query_replace': util.query_replace,
        'query_remove': util.query_remove
    }


@app.template_filter('slugify')
def slugify_filter(string):
    if not string:
        return ''
    return util.slugify(string)


@app.template_filter('display_name')
def display_name_filter(entity_or_data):
    if isinstance(entity_or_data, Entity):
        return display_name(entity_or_data)
    elif isinstance(entity_or_data, dict):
        return display_name(data_dict=entity_or_data)
    return ''


@app.template_filter('snippet')
def make_snippet(entity):
    if isinstance(entity, Entity):
        properties = entity.properties
        schema_label = entity.schema.label
    elif isinstance(entity, dict):
        properties = entity.get('properties')
        schema_label = entity.get('schema', {}).get('label')
    else:
        properties = {}
        schema_label = None

    if 'tagline' in properties:
        return properties.get('tagline').get('value')
    elif 'tagline' in properties:
        return properties.get('summary').get('value')
    elif schema_label is not None:
        return schema_label


@app.template_filter('portrait_url')
def make_portrait_url(entity):
    image_prop = entity.properties.get('image_full', None)
    if image_prop is None:
        return ''
    return util.IMAGE_URL % {
        'grano_host': app.config.get('GRANO_HOST').rstrip('/'),
        'file_pk': image_prop.get('value'),
        'config': 'portrait'
    }


@app.template_filter('thumbnail_url')
def make_thumbnail_url(entity):
    image_prop = entity.properties.get('image_thumb', None)
    if image_prop is None:
        return ''
    return util.IMAGE_URL % {
        'grano_host': app.config.get('GRANO_HOST'),
        'file_name': entity.properties['name']['value'],
        'file_pk': image_prop.get('value'),
        'config': 'thumbnail'
    }


@app.template_filter('relation_tagline')
def relation_tagline(relation):
    prop = relation_key_prop(relation)
    if prop is None:
        return relation.schema.get('label')
    return prop.value


@app.template_filter('relation_source')
def relation_source(relation):
    prop = relation_key_prop(relation)
    if prop is None:
        return None
    return prop.source_url


@app.template_filter('date')
def format_date(obj):
    if isinstance(obj, (date, datetime)):
        return obj.strftime('%d %b %Y')
    return ''


@app.template_filter('source_readable')
def format_source_readable(url):
    if url is None:
        return 'missing'
    parsed = urlparse(url)
    return parsed.hostname
