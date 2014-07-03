# TODO: Load contact persons - is that worth it, or polluting the database?
import logging

from granoclient.loader import Loader

from connectedafrica.core import grano
from connectedafrica.scrapers.util import read_json


log = logging.getLogger(__name__)


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
    loader = Loader(grano, source_url=record.get('source_url'))

    log.info('Loading: %s', record.get('LongName'))
    ent = create_entity(loader, record)

    for role in record.pop('AssociatedRoles'):
        role_desc = role.get('RoleDescription')
        alt = create_entity(loader, role)

        rel = loader.make_relation('jse_role', alt, ent)
        rel.set('role', role_desc)
        rel.save()


def load():
    records = read_json('jse.json') or {}
    for i, record in records.items():
        load_record(i, record)


if __name__ == '__main__':
    load()
