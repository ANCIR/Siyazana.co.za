from collections import OrderedDict
from operator import itemgetter

from flask import Blueprint, render_template, request, abort

from granoclient import NotFound

from connectedafrica.core import grano
from connectedafrica.util import slugify
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


def schemata_map(entity):
    '''
    Returns and OrderedDict that maps schemata to their label
    in alphabetical order.
    '''
    return OrderedDict(sorted(
        [(s['name'], s['label']) for s in entity.schemata],
        key=itemgetter(0)
    ))


@blueprint.route('/profile/<id>/<slug>')
def view(id, slug):
    try:
        entity = grano.entities.by_id(id)
        assert slugify(entity.properties['name']['value']) == slug
        schemata = schemata_map(entity)
        if 'popolo_person' in schemata:
            return person_profile(entity, schemata)
        elif 'popolo_organization' in schemata:
            return organization_profile(entity, schemata)
    except (AssertionError, NotFound):
        pass
    abort(404)


def person_profile(person, schemata):
    return render_template('person_profile.html',
                           person=person,
                           display_name=person_display_name(person),
                           source_map=source_map(person),
                           schemata_map=schemata)


def organization_profile(organization, schemata):
    return render_template('organization_profile.html',
                           organization=organization,
                           display_name=person_display_name(organization),
                           source_map=source_map(organization),
                           schemata_map=schemata)
