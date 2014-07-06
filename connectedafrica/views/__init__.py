from granoclient import Entity

from connectedafrica.core import app
from connectedafrica.views.base import blueprint as base_blueprint
from connectedafrica.views.browser import blueprint as browser_blueprint
from connectedafrica.views.profile import (blueprint as profile_blueprint,
                                           display_name)
from connectedafrica.views import helpers

app.register_blueprint(base_blueprint)
app.register_blueprint(browser_blueprint)
app.register_blueprint(profile_blueprint)


@app.context_processor
def inject_globals():
    return {
        'APP_NAME': app.config.get('APP_NAME'),
        'query_add': helpers.query_add,
        'query_remove': helpers.query_remove
    }


@app.template_filter('slugify')
def slugify_filter(string):
    if not string:
        return ''
    return helpers.slugify(string)


@app.template_filter('display_name')
def display_name_filter(entity_or_data):
    if isinstance(entity_or_data, Entity):
        return display_name(entity_or_data)
    elif isinstance(entity_or_data, dict):
        return display_name(data_dict=entity_or_data)
    return ''
