from collections import defaultdict

from connectedafrica.core import schemata
from connectedafrica.util.properties import Properties


def load_entity_relations(entity, filters={}):
    """ Get all relations associated with this entity. """
    relations = []
    for collection in (entity.inbound, entity.outbound):
        params = {'limit': 1000}
        collection = collection.query(params=params)
        for key, value in filters.items():
            collection = collection.filter(key, value)
        for relation in collection.results:
            relation.props = Properties(relation)
            relations.append(relation)
    return relations


def load_entity_relations_schemata(entity, filters={}):
    """ Get the facet counts for schemata associated with
    the relations of the given entity. """
    schemata_counts = defaultdict(int)
    for collection in (entity.inbound, entity.outbound):
        params = {'limit': 0, 'facet': 'schema'}
        collection = collection.query(params=params)
        facets = collection.data.get('facets', {}).get('schema', {})
        for schema, count in facets.get('results'):
            schemata_counts[schema['name']] += count
    return schemata_counts


def sort_key(relation):
    if 'date_start' in relation.props:
        return relation.props.date_start.value
    if 'date_end' in relation.props:
        return relation.props.date_end.value
    return '3000-' + relation.id


def get_time_key(relation):
    if 'date_start' in relation.props:
        return relation.props.date_start.value.year
    if 'date_end' in relation.props:
        return relation.props.date_end.value.year
    return 'Undated'


def load_relations(entity, schemata_filters):
    # TODO: allow for chunked, async load because crashing servers isn't nice
    # TODO: make grano return a sorted list that obeys limit and offset
    query_filters = {}
    if len(schemata_filters):
        query_filters['schema'] = ','.join(schemata_filters)
    schemata_all = schemata.by_obj('relation')
    schemata_counts = load_entity_relations_schemata(entity, query_filters)

    relations = {}

    for relation in load_entity_relations(entity, query_filters):
        if relation.target['id'] == entity.id:
            relation.other = relation.source
        else:
            relation.other = relation.target
        key = get_time_key(relation)
        if key not in relations:
            relations[key] = []
        relations[key].append(relation)

    for group, rels in relations.items():
        relations[group] = sorted(rels, key=sort_key)

    return {
        'schemata': schemata_all,
        'schemata_filters': schemata_filters,
        'schemata_counts': schemata_counts,
        'relations': sorted(relations.items(), reverse=True)
    }
