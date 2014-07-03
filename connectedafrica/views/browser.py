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
        'offset': request.args.get('offset', 20),
        'schema': request.args.get('schema', ''),
        'project': grano.slug
    }
    s, results = grano.client.get('/entities', params=params)
    paginator = Paginator(results)
    return render_template('browser.html',
                           paginator=paginator,
                           query=request.args.get('q', ''))
