from collections import OrderedDict, defaultdict
from operator import itemgetter

from flask import Blueprint, render_template, abort, request

from granoclient import NotFound

from connectedafrica.core import grano, schemata
from connectedafrica.views.util import convert_date_fields
from connectedafrica.views.util.properties import Properties


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


def make_relation_tagline(relation):
    schema = relation.schema['name']
    props = relation.properties
    tagline_prop = {
        'Membership': 'role',
        'Partnership': 'extent',
        'Personal': 'type',
        'FinancialInterest': 'nature',
        'Education': 'qualification_name'
    }[schema]
    if tagline_prop not in props:
        return relation.schema['label']
    tagline = props[tagline_prop]['value']
    if schema == 'Education' and 'level' in props:
        tagline = '%s (%s)' % (tagline, props['level']['value'])
    return tagline


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


def process_relations(entity):
    # TODO: allow for chunked, async load because crashing servers isn't nice
    # TODO: make grano return a sorted list that obeys limit and offset
    schemata_all = schemata.by_obj('relation')
    schemata_filters = request.args.getlist('schema')
    schemata_counts = defaultdict(int)

    temporal = []
    non_temporal = []

    def filter_relations(collection):
        params = {'limit': 0, 'facet': 'schema'}
        fc = collection.query(params=params)
        facets = fc.data.get('facets', {}).get('schema', {})
        for schema, count in facets.get('results'):
            schemata_counts[schema['name']] += count
        params = {'limit': 1000}
        collection = collection.query(params=params)
        if schemata_filters:
            collection = collection.filter('schema', ','.join(schemata_filters))
        return collection.results

    for relations in (entity.inbound, entity.outbound):
        for rel in filter_relations(relations):
            convert_date_fields(rel)
            if rel.properties.get('date_start', None):
                temporal.append(rel)
            else:
                non_temporal.append(rel)
            # add an 'other' attribute that refers to the
            # other entity in the relation, irrespective
            # of the direction of the relation
            if rel.target['id'] == entity.id:
                rel.other = rel.source
            else:
                rel.other = rel.target
    return {
        'schemata': schemata_all,
        'schemata_filters': schemata_filters,
        'schemata_counts': schemata_counts,
        'temporal': sorted(temporal,
                           key=lambda x: x.properties['date_start']['value']),
        'non_temporal': sorted(non_temporal,
                               key=lambda x: display_name(data_dict=x.target['properties'])),
    }


@blueprint.route('/profile/<id>/<slug>')
def view(id, slug):
    try:
        entity = grano.entities.by_id(id)
        convert_date_fields(entity, ['date_birth'])
        entity_schemata = schemata_map(entity)
        context = {
            'entity': entity,
            'properties': Properties(entity),
            'display_name': display_name(entity),
            'source_map': source_map(entity),
            'relations': process_relations(entity)
        }

        template = 'profile/base.html'
        if 'Person' in entity_schemata:
            template = 'profile/person.html'
        elif 'Organization' in entity_schemata:
            template = 'profile/organization.html'
        return render_template(template, **context)
    except (AssertionError, NotFound):
        pass
    abort(404)
