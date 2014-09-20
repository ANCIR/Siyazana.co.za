from flask import Blueprint, render_template, request
from restpager import Pager

from connectedafrica.core import grano


blueprint = Blueprint('browser', __name__)


@blueprint.route('/browse')
def view():
    query = grano.entities.query()
    query = query.filter('q', request.args.get('q', ''))
    query = query.filter('schema', request.args.getlist('schema'))
    query = query.filter('facet', 'schema')
    pager = Pager(query)

    schema_facet = query.data.get('facets').get('schema')
    schema_facet['active'] = request.args.getlist('schema')
    return render_template('browser.html',
                           schema_facet=schema_facet,
                           pager=pager,
                           query=request.args.get('q', ''))
