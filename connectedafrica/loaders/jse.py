import logging
from pprint import pprint
import json
from itertools import count

from granoclient.loader import Loader
import requests

from connectedafrica.core import grano


log = logging.getLogger(__name__)

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


def load_record(i):
    source_url = SOURCE_URL % i
    loader = Loader(grano, source_url=source_url)

    req = {
        'data': json.dumps({'issuerMasterId': i}),
        'headers': {'Content-Type': 'application/json'}
    }
    res = requests.post(ISSUER, **req)
    if res.status_code != 200 or res.json().get('GetIssuerResult') is None:
        return
    record = res.json().get('GetIssuerResult')
    res = requests.post(BUSINESS, **req)
    record['NatureOfBusiness'] = res.json().get('GetIssuerNatureOfBusinessResult')
    
    log.info('Loading: %s', record.get('LongName'))
    ent = create_entity(loader, record)

    res = requests.post(ASSOCIATED, **req)
    for role in res.json().get('GetIssuerAssociatedRolesResult'):
        role_desc = role.get('RoleDescription')
        alt = create_entity(loader, role)

        rel = loader.make_relation('jse_role', alt, ent)
        rel.set('role', role_desc)
        rel.save()

    #res = requests.post(SENS, **req)
    #pprint(record)


def load():
    for i in count(1):
        load_record(i)


if __name__ == '__main__':
    load()
