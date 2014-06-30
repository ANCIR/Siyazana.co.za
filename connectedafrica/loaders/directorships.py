import logging
import os
import unicodecsv as csv

from granoclient.loader import Loader

from connectedafrica.core import grano
from connectedafrica.loaders.util import parse_date, DATA_PATH


log = logging.getLogger(__name__)


def load_directorship_entry(loader, data):
    person = loader.make_entity(['popolo_entity', 'popolo_person'],
                                source_url=data['Source URL for information'])
    person.set('name', data['Person Name'])
    person.save()

    org = loader.make_entity(['popolo_entity', 'popolo_organization', 'popolo_area'],
                             source_url=data['Source URL for information'])
    org.set('name', data['Organisation Name'])
    # TODO: not sure if this is the correct use of classification?
    org.set('org_classification', data['Org type'])
    org.set('physical_address', data['Address'])
    org.set('org_identifier', data['Registration number'])
    
    relation = loader.make_relation('popolo_membership', person, org,
                                    source_url=data['Source URL for information'])
    relation.set('role', data['Role description'])
    start_date = parse_date(data['Director since'])
    end_date = parse_date(data['Director until'])
    if start_date is not None:
        relation.set('start_date', start_date)
    if end_date is not None:
        relation.set('end_date', end_date)
    relation.save()


def load():
    loader = Loader(grano, source_url=None)
    csv_path = os.path.join(DATA_PATH, 'directorships.csv')
    with open(csv_path) as f:
        for row in csv.DictReader(f):
            load_directorship_entry(loader, row)


if __name__ == '__main__':
    load()
