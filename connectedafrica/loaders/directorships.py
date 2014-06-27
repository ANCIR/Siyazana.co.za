from datetime import datetime
import logging
import os
from pprint import pprint
import unicodecsv as csv

from granoclient.loader import Loader

from connectedafrica.core import grano


log = logging.getLogger(__name__)


DATE_FORMAT = '%m/%d/%Y'
FIELD_NAMES = ('Person Name', 'Organisation Name', 'Org type', 'Address',
               'Role description', 'Registration number', 'Status',
               'Director since', 'Director until', 'Source URL for information')


def _parse_date(datestr):
    try:
        return datetime.strptime(datestr, DATE_FORMAT)
    except ValueError:
        return None


# TODO: don't create duplicate entities
# Registration number + country can be used as ID for organization
def load_directorship_entry(loader, data):
    person = loader.make_entity(['popolo_entity', 'popolo_person'],
                                source_url=data['Source URL for information'])
    person.set('name', data['Person Name'])
    person.save()

    org = loader.make_entity(['popolo_entity', 'popolo_organization'],
                             source_url=data['Source URL for information'])
    org.set('name', 'Organisation Name')
    # TODO: not sure if this is the correct use of classification?
    org.set('org_classification', data['Org type'])
    org.set('physical_address', data['Address'])
    org.set('org_identifier', data['Registration number'])
    
    relation = loader.make_relation('popolo_membership', person, org)
    relation.set('role', data['Role description'])
    start_date = _parse_date(data['Director since'])
    end_date = _parse_date(data['Director until'])
    if start_date is not None:
        relation.set('start_date', start_date)
    if end_date is not None:
        relation.set('end_date', end_date)
    relation.save()


def load():
    loader = Loader(grano, source_url=None)
    csv_path = os.path.join(os.path.dirname(__file__),
                            '..', '..', 'data', 'directorships.csv')
    with open(csv_path) as f:
        for row in csv.DictReader(f, FIELD_NAMES):
            load_directorship_entry(loader, row)


if __name__ == '__main__':
    load()
