from datetime import datetime
from urllib import urlencode
from operator import itemgetter

from flask import request
from slugify import slugify as _slugify

from connectedafrica.core import grano, url_for


STOPWORDS = ['of', 'and', 'for', 'the', 'a', 'in']
IMAGE_URL = '%(grano_host)s/api/1/files/_image/%(file_name)s-%(file_pk)s-%(config)s.png' 
DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'


def _enc(arg):
    qs = urlencode([(k, v.encode('utf-8')) for k, v in arg])
    url = url_for(request.endpoint, **request.view_args)
    if len(qs):
        url = '?' + qs
    return url


def query_add(arg, val):
    args = request.args.items(multi=True) + [(arg, val)]
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


def convert_date_fields(obj, fields=('date_start', 'date_end')):
    for field in fields:
        if field in obj.properties:
            obj.properties[field]['value'] = datetime.strptime(
                obj.properties[field]['value'],
                DATETIME_FORMAT
            ).date()


def get_schemata(obj_type, include_hidden=False):
    """ Returns all schemata on grano for either relations
        or entities. By default this does not include
        hidden schemata. """
    key = (obj_type, include_hidden)
    if key not in get_schemata._cache:
        schemata = [s for s in grano.schemata if (include_hidden
                    or not s.hidden) and s.obj == obj_type]
        get_schemata._cache[key] = sorted(schemata, key=itemgetter('label'))
    return get_schemata._cache[key]
get_schemata._cache = {}
