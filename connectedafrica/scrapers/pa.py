import logging
from pprint import pprint

import requests

from connectedafrica.scrapers.util import MultiCSV


log = logging.getLogger('pa')

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


def load_interests(csv, person, register):
    for report, sections in register.items():
        for section, items in sections.items():
            for item in items:
                if 'DIRECTORSHIP' in section:
                    company = item.get('Directorship/Partnership')
                    if company is None or not len(company.strip()):
                        continue
                    data = {
                        'person_name': person['name'],
                        'source_url': person['source_url'],
                        'report': report,
                        'company_name': company.strip(),
                        'company_type': item.get('Type of Business')
                        }
                    csv.write('pa_directorships.csv', data)
                if 'FINANCIAL INTERESTS' in section:
                    company = item.get('Name of Company')
                    if company is None or not len(company.strip()):
                        continue
                    data = {
                        'person_name': person['name'],
                        'source_url': person['source_url'],
                        'report': report,
                        'company_name': company.strip(),
                        'nature': item.get('Nature'),
                        'number': item.get('No'),
                        'nominal_value': item.get('Nominal Value')
                        }
                    csv.write('pa_financial.csv', data)


def load_persons(api_meta, csv, orgs):
    api_url = api_meta.get('persons_api_url') + '?per_page=50'
    for person in crawl_pages(api_url):
        name = person.get('name').strip()
        if name is None:
            continue
        name = name.strip()
        if not len(name):
            continue
        log.info("Loading person: %s", name)
        data = {
            'name': name,
            'popit_id': person.get('id'),
            'source_url': person.get('url'),
            'pa_url': person.get('pa_url'),
            'given_name': person.get('given_name'),
            'family_name': person.get('family_name'),
            'summary': person.get('summary'),
            'telephone_number': None,
            'email': None
        }

        for contact in person.get('contact_details', []):
            if contact.get('type') == 'voice':
                data['telephone_number'] = contact.get('value')
            if contact.get('type') == 'email':
                data['email'] = contact.get('value')

        csv.write('pa_persons.csv', data)

        load_interests(csv, data, person.get('interests_register', {}))

        for name in person.get('other_names', []):
            csv.write('pa_aliases.csv', {
                'alias': name['name'],
                'canonical': data['name'],
                'source_url': data['source_url']
                })

        for membership in person.pop('memberships'):
            org_id = membership.get('organization_id')
            if org_id not in orgs:
                continue
            mem = {
                'source_url': data['source_url'],
                'organization_id': org_id,
                'organization_name': orgs[org_id].get('name'),
                'role': membership.get('role'),
                'person_name': data['name'],
                'start_date': membership.get('start_date'),
                'end_date': membership.get('end_date')
            }
            csv.write('pa_memberships.csv', mem)


def load_organizations(api_meta, csv):
    orgs = {}
    api_url = api_meta.get('organizations_api_url') + '?per_page=50'

    for org in crawl_pages(api_url):
        log.info("Loading organisation: %s", org.get('name'))
        clazz = org.get('classification')
        data = {
            'name': org.get('name'),
            'popit_id': org.get('id'),
            'source_url': org.get('url'),
            'pa_url': org.get('pa_url'),
            'org_category': org.get('category'),
            'org_classification': clazz
        }

        if clazz == 'Party':
            csv.write('pa_parties.csv', data)
            orgs[org.get('id')] = data
        elif 'Committee' in clazz:
            csv.write('pa_committees.csv', data)
            orgs[org.get('id')] = data
    return orgs


def load():
    csv = MultiCSV()
    api_meta = requests.get(INSTANCE_URL).json().get('meta')
    orgs = load_organizations(api_meta, csv)
    #orgs = {}
    load_persons(api_meta, csv, orgs)


if __name__ == '__main__':
    load()
