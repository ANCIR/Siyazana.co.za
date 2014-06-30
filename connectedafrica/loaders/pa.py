import logging
from pprint import pprint

import requests
from granoclient.loader import Loader

from connectedafrica.core import grano


log = logging.getLogger(__name__)

INSTANCE_URL = 'http://za-new-import.popit.mysociety.org/api/v0.1/'


def crawl_pages(url):
    """ Make a paginated collection on the web into a generator. """
    while True:
        res = requests.get(url)
        data = res.json()
        for result in data.get('result', []):
            yield result
        if not data.get('has_more'):
            return
        url = data.get('next_url')


def load_persons(api_meta, loader, orgs):
    api_url = api_meta.get('persons_api_url') + '?per_page=200'
    for person in crawl_pages(api_url):
        log.info("Loading person: %s", person.get('name'))
        
        source_url = person.pop('url')
        ent = loader.make_entity(['popolo_entity', 'popolo_person', 'details'],
                                 source_url=source_url)
        ent.set('name', person.pop('name'))
        ent.set('popit_id', person.pop('id'))
        if person.get('given_name') is not None:
            ent.set('given_name', person.pop('given_name'))
        if person.get('family_name') is not None:
            ent.set('family_name', person.pop('family_name'))
        if person.get('summary') is not None:
            ent.set('summary', person.pop('summary'))
        ent.set('pa_url', person.pop('pa_url'))
        ent.set('popit_api_url', source_url)

        for contact in ent.pop('contacts'):
            if contact.get('type') == 'voice':
                ent.set('telephone_number', contact.get('value'))
            if contact.get('type') == 'email':
                ent.set('email', contact.get('value'))

        ent.save()

        for membership in person.pop('memberships'):
            if membership.get('organization_id') not in orgs:
                continue
            org = orgs[membership.get('organization_id')]
            rel = loader.make_relation('popolo_membership', ent, org)
            rel.set('role', membership.pop('role'))
            if membership.get('start_date') is not None:
                rel.set('start_date', membership.pop('start_date'))
            if membership.get('end_date') is not None:
                rel.set('end_date', membership.pop('endt_date'))
            rel.save()

        #print person.keys()
        pprint(person)


def load_organizations(api_meta, loader):
    orgs = {}
    api_url = api_meta.get('organizations_api_url') + '?per_page=200'

    for org in crawl_pages(api_url):
        clazz = org.get('classification')
        if clazz in ['Constituency Area', 'Election List', 'Constituency Office']:
            continue

        schemata = ['popolo_entity', 'popolo_organization']
        if clazz == 'Party':
            schemata.append('political_party')
        elif 'Committee' in clazz:
            schemata.append('political_committee')
        log.info("Loading organisation: %s", org.get('name'))
        
        source_url = org.pop('url')
        org_id = org.pop('id')
        ent = loader.make_entity(schemata, source_url=source_url)
        ent.set('name', org.pop('name'))
        ent.set('popit_id', org_id)
        ent.set('pa_url', org.pop('pa_url'))

        ent.set('org_category', org.pop('category', None))
        ent.set('org_classification', org.pop('classification'))
        
        ent.save()
        orgs[org_id] = ent

    return orgs


def load():
    loader = Loader(grano, source_url=INSTANCE_URL)
    api_meta = requests.get(INSTANCE_URL).json().get('meta')
    #orgs = load_organizations(api_meta, loader)
    orgs = {}
    load_persons(api_meta, loader, orgs)


if __name__ == '__main__':
    load()
