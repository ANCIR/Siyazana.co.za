from flask import Blueprint, render_template, request

from connectedafrica.core import grano
from connectedafrica.views.paginator import Paginator


blueprint = Blueprint('browser', __name__)


@blueprint.route('/browse')
def view():
    limit = 15
    params = {
        'q': request.args.get('q', ''),
        'limit': limit,
        'offset': request.args.get('offset', 0),
        'schema': request.args.getlist('schema'),
        'project': grano.slug,
        'facet': 'schema'
    }
    s, results = grano.client.get('/entities', params=params)
    schema_facet = results.get('facets').get('schema')
    schema_facet['active'] = request.args.getlist('schema')
    paginator = Paginator(results)
    return render_template('browser.html',
                           schema_facet=schema_facet,
                           paginator=paginator,
                           query=request.args.get('q', ''))
