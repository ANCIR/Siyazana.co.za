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
    features = [p for p in pages if p.meta.get('featured')]
    return render_template('index.html', features=features,
                           schemata=results.get('facets').get('schema'))


@blueprint.route('/pages/<path:path>/')
def page(path):
    page = pages.get_or_404(path)
    menu = [p for p in pages if p.meta.get('menutitle')]
    menu = sorted(menu, key=lambda p: p.meta.get('menuindex'))
    children = [p for p in pages if p.meta.get('parent') == page.path]
    template = page.meta.get('template', 'pages.html')
    return render_template(template, page=page, menu=menu,
                           children=children)
