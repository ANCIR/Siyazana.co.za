#
# Scrape the Johannesburg Stock Exchange Listed Companies.
#
# This scraper runs against a JSON interface provided by JSE and retrieve
# data related to all listed companies; the companies related to them
# (their Auditors, Sponsors etc.); and contact persons for some of them.
#
# TODO: Load contact persons - is that worth it, or polluting the database?

import logging
#from pprint import pprint
import json

from thready import threaded
from granoclient.loader import Loader
import requests

from connectedafrica.core import grano
from connectedafrica.loaders.util import write_json, read_json


log = logging.getLogger(__name__)

INDEX = 'https://www.jse.co.za/_vti_bin/JSE/CustomerRoleService.svc/GetAllIssuers'
ISSUER = 'https://www.jse.co.za/_vti_bin/JSE/CustomerRoleService.svc/GetIssuer'
BUSINESS = 'https://www.jse.co.za/_vti_bin/JSE/CustomerRoleService.svc/GetIssuerNatureOfBusiness'
ASSOCIATED = 'https://www.jse.co.za/_vti_bin/JSE/CustomerRoleService.svc/GetIssuerAssociatedRoles'
SENS = 'https://www.jse.co.za/_vti_bin/JSE/SENSService.svc/GetSensAnnouncementsByIssuerMasterId'
SOURCE_URL = 'https://www.jse.co.za/current-companies/listed-companies/issuer-profile?issuermasterid=%s'


def create_entity(loader, record):
    ent = loader.make_entity(['details', 'jse_company'])
    
    ent.set('name', record.pop('LongName'))

    ent.set('jse_code', record.pop('AlphaCode'))
    ent.set('jse_status', record.pop('Status'))
    ent.set('jse_role', record.pop('RoleDescription'))
    ent.set('jse_registration_number', record.pop('RegistrationNumber'))
    ent.set('jse_nature_business', record.pop('NatureOfBusiness', None))

    ent.set('website', record.pop('Website'))
    ent.set('email', record.pop('EmailAddress'))
    ent.set('telephone_number', record.pop('TelephoneNumber'))
    ent.set('fax_number', record.pop('FaxNumber'))
    ent.set('postal_address', record.pop('PostalAddress'))
    ent.set('physical_address', record.pop('PhysicalAddress'))

    ent.save()
    return ent


def load_record(i, record):
    """ Load an individual record to grano. """
    source_url = SOURCE_URL % i
    loader = Loader(grano, source_url=source_url)

    log.info('Loading: %s', record.get('LongName'))
    ent = create_entity(loader, record)

    for role in record.pop('AssociatedRoles'):
        role_desc = role.get('RoleDescription')
        print role_desc
        alt = create_entity(loader, role)

        rel = loader.make_relation('jse_role', alt, ent)
        rel.set('role', role_desc)
        rel.save()


def load():
    records = read_json('jse.json') or {}
    for i, record in records.items():
        load_record(i, record)


def scrape_record(records, i):
    """ Scrape data regarding a single listed company. """
    req = {
        'data': json.dumps({'issuerMasterId': i}),
        'headers': {'Content-Type': 'application/json'}
    }
    res = requests.post(ISSUER, **req)
    if res.status_code != 200 or res.json().get('GetIssuerResult') is None:
        return
    
    record = res.json().get('GetIssuerResult')
    log.info('Scraping: %s', record.get('LongName'))
    
    try:
        res = requests.post(BUSINESS, **req)
        res = res.json()
        record['NatureOfBusiness'] = res.get('GetIssuerNatureOfBusinessResult')
    except Exception, e:
        log.exception(e)

    res = requests.post(ASSOCIATED, **req)
    res = res.json()
    record['AssociatedRoles'] = res.get('GetIssuerAssociatedRolesResult')

    records[i] = record


def scrape_index(records):
    """ Get a list of listed companies. """
    req = {
        'data': json.dumps({}),
        'headers': {'Content-Type': 'application/json'}
    }
    res = requests.post(INDEX, **req)
    for row in res.json():
        master_id = str(row.get('MasterID'))
        if master_id not in records:
            yield master_id


def scrape():
    records = read_json('jse.json') or {}
    threaded(scrape_index(records),
             lambda i: scrape_record(records, i),
             num_threads=30)
    write_json('jse.json', records)


if __name__ == '__main__':
    scrape()
    load()
