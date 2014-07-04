from collections import OrderedDict

from flask import Blueprint, render_template, request, abort

from granoclient import NotFound

from connectedafrica.core import grano
from connectedafrica.views.paginator import Paginator


blueprint = Blueprint('profile', __name__)


def person_display_name(person):
    '''
    Return the most appropriate name for display, depending
    on which properties have been set.
    '''
    if 'name_short' in person.properties:
        return person.properties['name_short']['value']
    elif 'name_full' in person.properties:
        return person.properties['name_full']['value']
    elif 'given_name' in person.properties and \
            'family_name' in person.properties:
        return '%s %s' % (person.properties['given_name']['value'],
                          person.properties['family_name']['value'])
    else:
        return person.properties['name']['value'].title()


def source_map(entity):
    '''
    Returns an OrderedDict that maps sources to their citation
    number in alphabetical order.
    '''
    sources = set(v['source_url'] for v in entity.properties.values())
    return OrderedDict((s, i + 1) for i, s in enumerate(sorted(sources)))


@blueprint.route('/person/<name>')
def person_profile(name):
    try:
        entity = list(grano.entities.query(params={'limit': 1}) \
                                    .filter('schema', 'popolo_person') \
                                    .filter('q', name) \
                                    .results)[0]
        return render_template('person_profile.html',
                               person=entity,
                               display_name=person_display_name(entity),
                               source_map=source_map(entity))
    except NotFound:
        abort(404)
