from collections import OrderedDict

from flask import Blueprint, render_template, redirect, url_for
from granoclient import NotFound


from connectedafrica.core import grano
from connectedafrica import util
from connectedafrica.util.properties import Properties
from connectedafrica.util.relations import load_relations


blueprint = Blueprint('profile', __name__)


def display_name(entity=None, data_dict=None):
    '''
    Return the most appropriate name for display, depending
    on which properties have been set.
    '''
    if entity is None and data_dict is None:
        raise TypeError("One of 'entity' or 'data_dict' is required")
    if entity:
        properties = entity.properties
    else:
        properties = data_dict
    if 'display_name' in properties:
        return properties['display_name']['value']
    elif 'full_name' in properties:
        return properties['full_name']['value']
    elif 'given_name' in properties and \
            'family_name' in properties:
        return '%s %s' % (properties['given_name']['value'],
                          properties['family_name']['value'])
    else:
        return properties['name']['value'].title()


def source_map(entity):
    '''
    Returns an OrderedDict that maps sources to their citation
    number in alphabetical order.
    '''
    sources = set(v['source_url'] for v in entity.properties.values())
    return OrderedDict((s, i + 1) for i, s in enumerate(sorted(sources)))


@blueprint.route('/profile/<id>')
def fwd_view(id):
    entity = grano.entities.by_id(id)
    name = entity.properties.get('name', {}).get('value', 'x')
    slug = util.slugify(name)
    return redirect(url_for('.view', id=id, slug=slug))


@blueprint.route('/profile/<id>/<slug>')
def view(id, slug):
    entity = grano.entities.by_id(id)
    relation_sections = load_relations(entity, id, slug)

    template = 'profile/base.html'
    if entity.schema.name == 'Person':
        template = 'profile/person.html'
    elif entity.schema.name == 'Organization':
        template = 'profile/organization.html'
    return render_template(template,
                           entity=entity,
                           properties=Properties(entity),
                           display_name=display_name(entity),
                           source_map=source_map(entity),
                           relation_sections=relation_sections)
