from flask import Blueprint, render_template, request
from restpager import Pager

from connectedafrica.core import grano, schemata


blueprint = Blueprint('browser', __name__)


@blueprint.route('/search')
def view():
        query = grano.entities.query()
        query = query.filter('q', request.args.get('q', ''))
        schema_active = request.args.getlist('schema')
        main_schema = None
        if not len(schema_active):
            # TODO: get this from schema 'meta':
            schema_active = ['Person', 'Organization', 'Company',
                             'NonProfit', 'EducationalInstitution']
        else:
            main_schema = schemata.by_name(schema_active[0])
        query = query.filter('schema', schema_active)
        query = query.filter('sort', '-degree')
        pager = Pager(query)
        return render_template('browser.html',
                               main_schema=main_schema,
                               pager=pager)
