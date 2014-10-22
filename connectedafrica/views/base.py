from flask import Blueprint, render_template, request

from connectedafrica.core import pages, grano, cache


blueprint = Blueprint('base', __name__)


def get_top(schema):
    query = grano.entities.query()
    query = query.filter('schema', schema)
    query = query.filter('sort', '-degree')
    return query.limit(7)


@blueprint.route('/')
@cache.cached()
def index():
    orgs = get_top(['Organization', 'Company', 'NonProfit'])
    people = get_top('Person')
    return render_template('index.html', orgs=orgs, people=people)


@blueprint.route('/pages/<path:path>.html')
@cache.cached()
def page(path):
    page = pages.get_or_404(path)
    menu = [p for p in pages if p.meta.get('menutitle')]
    menu = sorted(menu, key=lambda p: p.meta.get('menuindex'))
    children = [p for p in pages if p.meta.get('parent') == page.path]
    template = page.meta.get('template', 'pages.html')
    return render_template(template, page=page, menu=menu,
                           children=children)
