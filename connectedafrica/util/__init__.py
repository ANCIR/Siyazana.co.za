from datetime import datetime
from urllib import urlencode

from flask import request
from slugify import slugify as _slugify

from connectedafrica.core import url_for

STOPWORDS = ['of', 'and', 'for', 'the', 'a', 'in']
IMAGE_URL = '%(grano_host)s/api/1/files/%(file_pk)s/_image/%(config)s.png'
MAJOR_ENTITY_SCHEMATA = set((
    'Person', 'LegalCase', 'PublicCompany',
    'Committee', 'NonProfit', 'PoliticalParty',
    'EducationalInstitution'
))


def _enc(arg):
    qs = urlencode([(k, v.encode('utf-8')) for k, v in arg])
    url = url_for(request.endpoint, **request.view_args)
    if len(qs):
        url = '?' + qs
    return url


def query_add(arg, val):
    args = request.args.items(multi=True) + [(arg, val)]
    return _enc(args)


def query_replace(arg, val):
    args = request.args.items(multi=True)
    args = [(a, b) for (a, b) in args if a != arg]
    args = args + [(arg, val)]
    return _enc(args)


def query_remove(arg, val):
    args = request.args.items(multi=True)
    args = [(a, b) for (a, b) in args if a != arg or b != val]
    return _enc(args)


def slugify(text):
    slug = _slugify(text)
    for stopword in STOPWORDS:
        slug = slug.replace('-%s-' % stopword, '-')
    return slug


def guess_major_schema(schemata):
    """ Returns the most specific schema of an entity. E.g.
        a person entity has schemata base and Person where the
        most specific schema is Person."""
    for schema in schemata:
        if schema['name'] in MAJOR_ENTITY_SCHEMATA:
            return schema['name']
    return None
