from datetime import datetime
import logging
import os
import unicodecsv as csv

from granoclient.loader import Loader

from connectedafrica.core import grano
from connectedafrica.loaders.util import parse_date, DATA_PATH


log = logging.getLogger(__name__)

ALTERNATE_DATE_FORMAT = '%d.%m.%Y'


def parse_date_range(rangestr):
    # TODO: split spreadsheet column into 'Start date of hearing' +
    # 'End date of hearing'? This is very error prone.
    format = '%d %B %Y'
    days, month, year = rangestr.rsplit(' ', 2)
    start_day, end_day = [s.strip() for s in days.split('-')]
    start_date = datetime.strptime('%s %s %s' % (start_day, month, year),
                                   format)
    end_date = datetime.strptime('%s %s %s' % (end_day, month, year),
                                 format)
    return start_date, end_date


def load_litigation_entry(loader, data):
    entity = loader.make_entity(['popolo_entity'],
                                source_url=data['Source URL'])
    entity.set('name', data['Entity'])
    entity.save()

    case = loader.make_entity(['legal_case', 'popolo_area'],
                              source_url=data['Source URL'])
    case.set('name', data['Case No.'])
    case.set('citation', data['Citation'])
    case.set('title', data['Title'])
    if not data['Date decided']:
        date_decided = None
    elif '.' in data['Date decided']:
        date_decided = parse_date(data['Date decided'], ALTERNATE_DATE_FORMAT)
    else:
        date_decided = parse_date(data['Date decided'])
    if not data['Date heard']:
        start_date = end_date = None
    elif '.' in data['Date heard']:
        start_date = end_date = parse_date(data['Date heard'], ALTERNATE_DATE_FORMAT)
    elif '-' in data['Date heard']:
        start_date, end_date = parse_date_range(data['Date heard'])
    else:
        start_date = end_date = parse_date(data['Date heard'])
    # set non-None dates
    if date_decided is not None:
        case.set('date_decided', date_decided)
    if start_date is not None:
        case.set('start_date', start_date)
    if end_date is not None:
        case.set('end_date', end_date)
    case.save()
    
    relation = loader.make_relation('popolo_membership', entity, case,
                                    source_url=data['Source URL'])
    relation.set('role', data['Role'])
    relation.save()


def load():
    loader = Loader(grano, source_url=None)
    csv_path = os.path.join(DATA_PATH, 'litigation.csv')
    with open(csv_path) as f:
        for row in csv.DictReader(f):
            load_litigation_entry(loader, row)


if __name__ == '__main__':
    load()