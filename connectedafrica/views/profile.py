from collections import OrderedDict
from operator import itemgetter

from flask import Blueprint, render_template, abort, request

from granoclient import NotFound

from connectedafrica.core import grano
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


def schemata_map(entity):
    '''
    Returns and OrderedDict that maps schemata to their label
    in alphabetical order.
    '''
    return OrderedDict(sorted(
        [(s['name'], s['label']) for s in entity.schemata
         if not s['hidden']],
        key=itemgetter(0)
    ))


@blueprint.route('/profile/<id>/<slug>')
def view(id, slug):
    try:
        entity = grano.entities.by_id(id)
        entity_schemata = schemata_map(entity)
        relation_schemata = request.args.getlist('schema')
        grouper = request.args.get('grouper')
        context = {
            'entity': entity,
            'properties': Properties(entity),
            'display_name': display_name(entity),
            'source_map': source_map(entity),
            'relations': load_relations(entity, grouper,
                                        relation_schemata)
        }

        print context

        template = 'profile/base.html'
        if 'Person' in entity_schemata:
            template = 'profile/person.html'
        elif 'Organization' in entity_schemata:
            template = 'profile/organization.html'
        return render_template(template, **context)
    except (AssertionError, NotFound):
        pass
    abort(404)
