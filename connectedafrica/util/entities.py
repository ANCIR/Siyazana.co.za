from connectedafrica.core import grano, schemata


def schema_facets(q=None):
    facets = []
    qy = grano.entities.query().limit(0)
    qy = qy.filter('facet', 'schema')
    if q:
        qy = qy.filter('q', q)
    qy = qy.limit(0)
    schema_types = qy.data.get('facets', {}).get('schema', {})
    for (schema, count) in schema_types.get('results', []):
        schema = schemata.by_name(schema.get('name'))
        facets.append((schema, count))
    return facets

