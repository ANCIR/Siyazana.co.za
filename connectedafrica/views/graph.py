import json

from flask import Blueprint, request, make_response

from connectedafrica.core import grano, cache


blueprint = Blueprint('graph', __name__)


@cache.memoize()
def get_graph(query):
    api_url = grano.api_url + '/query'
    status, data = grano.client.get(api_url, params={'query': query})
    return json.dumps(data)


@blueprint.route('/graph')
def proxy():
    data = get_graph(request.args.get('query'))
    res = make_response(data)
    res.headers['Content-Type'] = 'application/json'
    return res
