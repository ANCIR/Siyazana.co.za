from flask import request
from urllib import urlencode
from slugify import slugify as _slugify

from connectedafrica.core import url_for

STOPWORDS = ['of', 'and', 'for', 'the', 'a', 'in']


def _enc(arg):
    qs = urlencode([(k, v.encode('utf-8')) for k, v in arg])
    url = url_for(request.endpoint)
    if len(qs):
        url = '?' + qs
    return url


def query_add(arg, val):
    args = request.args.items() + [(arg, val)]
    return _enc(args)


def query_remove(arg, val):
    args = request.args.items()
    args = [(a, b) for (a, b) in args if a != arg or b != val]
    return _enc(args)


def slugify(text):
    slug = _slugify(text)
    for stopword in STOPWORDS:
        slug = slug.replace('-%s-' % stopword, '-')
    return slug
