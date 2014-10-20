from restpager import Pager

from connectedafrica.core import grano, schemata
from connectedafrica.util.properties import Properties


def load_relations(entity, id, slug):
    relation_sections = []
    q = grano.relations.query().limit(0)
    q = q.filter('facet', 'schema').filter('entity', id)
    schema_types = q.data.get('facets', {}).get('schema', {})
    for (schema, count) in schema_types.get('results', []):
        iq = grano.relations.query().limit(15)
        iq = iq.filter('schema', schema.get('name'))
        pager = Pager(iq, name=schema.get('name'), id=id, slug=slug)
        relations = []

        for r in pager:
            r.props = Properties(r)
            r.other = r.source if r.target.id == id else r.target
            relations.append(r)

        data = {
            'schema': schemata.by_name(schema.get('name')),
            'count': count,
            'pager': pager,
            'relations': relations
        }

        relation_sections.append(data)

    return sorted(relation_sections,
                  key=lambda r: r['schema'].label)

