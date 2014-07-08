import re
from flask import request
from urllib import urlencode
from unicodedata import normalize


from connectedafrica.core import url_for


_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')


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


def slugify(text, delim=u'-'):
    """
    Generates an ASCII-only slug.
    Source: http://flask.pocoo.org/snippets/5/
    """
    result = []
    for word in _punct_re.split(text.lower()):
        word = normalize('NFKD', word).encode('ascii', 'ignore')
        if word:
            result.append(word)
    return unicode(delim.join(result))
