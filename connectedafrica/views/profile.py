from collections import OrderedDict
from operator import itemgetter

from flask import Blueprint, render_template, abort

from granoclient import NotFound

from connectedafrica.core import grano
from connectedafrica.views.util import slugify


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


def split_relations(entity):
    temporal = []
    non_temporal = []
    for relations in (entity.inbound, entity.outbound):
        for rel in relations:
            if rel.properties.get('date_start', None):
                temporal.append(rel)
            else:
                non_temporal.append(rel)
    return sorted(temporal, key=lambda x: x.properties['date_start']), \
           sorted(non_temporal,
                  key=lambda x: display_name(data_dict=x.target['properties']))


@blueprint.route('/profile/<id>/<slug>')
def view(id, slug):
    try:
        entity = grano.entities.by_id(id)
        assert slugify(entity.properties['name']['value']) == slug
        schemata = schemata_map(entity)
        temporal_rels, non_temporal_rels = split_relations(entity)
        context = {
            'entity': entity,
            'display_name': display_name(entity),
            'source_map': source_map(entity),
            'schemata_map': schemata,
            'relations': {'temporal': temporal_rels,
                          'non_temporal': non_temporal_rels}
        }
        if 'Person' in schemata:
            return person_profile(entity, context)
        elif 'Organization' in schemata:
            return organization_profile(entity, context)
        else:
            return render_template('profile_base.html',
                                   **context)
    except (AssertionError, NotFound):
        pass
    abort(404)


def person_profile(person, context):
    return render_template('person_profile.html',
                           **context)


def organization_profile(organization, context):
    return render_template('organization_profile.html',
                           **context)
