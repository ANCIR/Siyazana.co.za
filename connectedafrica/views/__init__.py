from datetime import datetime, date
from urlparse import urlparse

from flask import request, url_for
from granoclient import Entity

from connectedafrica.core import app, grano
from connectedafrica.views.base import blueprint as base_blueprint
from connectedafrica.views.browser import blueprint as browser_blueprint
from connectedafrica.views.profile import blueprint as profile_blueprint
from connectedafrica.views.graph import blueprint as graph_blueprint
from connectedafrica.views.profile import display_name
from connectedafrica import util
from connectedafrica.util.entities import schema_facets


app.register_blueprint(base_blueprint)
app.register_blueprint(browser_blueprint)
app.register_blueprint(profile_blueprint)
app.register_blueprint(graph_blueprint)


@app.context_processor
def inject_globals():
    query_text = request.args.get('q', '')
    sidebar_schemata = []
    
    for (schema, count) in schema_facets(q=query_text):
        active = schema.name in request.args.getlist('schema')
        url = url_for('browser.view', q=query_text, schema=schema.name)
        sidebar_schemata.append((schema, url, active, count))

    return {
        'APP_NAME': app.config.get('APP_NAME'),
        'PROJECT_API': grano.api_url,
        'query_text': query_text,
        'sidebar_schemata': sidebar_schemata,
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


@app.template_filter('relation_source')
def relation_source(relation):
    for name, prop in relation.properties.items():
        if prop.get('source_url') is not None:
            return prop.get('source_url')


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
    source_name = parsed.hostname
    if source_name in app.config.get('SOURCE_NAMES', {}):
        source_name = app.config.get('SOURCE_NAMES', {}).get(source_name)
    return source_name
