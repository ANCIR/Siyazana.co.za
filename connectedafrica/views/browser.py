from flask import Blueprint, render_template, request
from restpager import Pager

from connectedafrica.core import grano, schemata


blueprint = Blueprint('browser', __name__)


@blueprint.route('/browse')
def view():
        query = grano.entities.query()
        query = query.filter('q', request.args.get('q', ''))
        schema_active = request.args.getlist('schema')
        if not len(schema_active):
            # TODO: get this from schema 'meta':
            schema_active = ['Person', 'Organization', 'Company',
                             'NonProfit', 'EducationalInstitution']
        query = query.filter('schema', schema_active)
        query = query.filter('facet', 'schema')
        query = query.filter('sort', '-degree')
        pager = Pager(query)

        facet = query.data.get('facets').get('schema').get('results')
        schema_facet = {
            'results': [(schemata.by_name(s['name']), c) for s, c in facet],
            'active': request.args.getlist('schema')
        }
        return render_template('browser.html',
                               schema_facet=schema_facet,
                               pager=pager,
                               query=request.args.get('q', ''))


@blueprint.route('/organizations')
def organizations():
        query = grano.entities.query()
        query = query.filter('q', request.args.get('q', ''))
        query = query.filter('schema', ['Organization', 'Company'])
        query = query.filter('sort', '-degree')
        query = query.limit(27)
        pager = Pager(query)

        return render_template('organizations.html',
                               pager=pager,
                               query=request.args.get('q', ''))
