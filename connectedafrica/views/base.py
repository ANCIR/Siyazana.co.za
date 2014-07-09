from flask import Blueprint, render_template

from connectedafrica.core import pages, grano


blueprint = Blueprint('base', __name__)


@blueprint.route('/')
def index():
    params = {
        'limit': 0,
        'project': grano.slug,
        'facet': 'schema'
    }
    s, results = grano.client.get('/entities', params=params)
    return render_template('index.html',
                           schemata=results.get('facets').get('schema'))


@blueprint.route('/pages/<path:path>/')
def page(path):
    page = pages.get_or_404(path)
    template = page.meta.get('template', 'pages.html')
    return render_template(template, page=page)
