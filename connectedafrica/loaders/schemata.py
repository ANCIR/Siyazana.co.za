import logging
import os
import yaml

from connectedafrica.core import grano, NotFound


log = logging.getLogger(__name__)


def load_file():
    schema_file = os.path.join(os.path.dirname(__file__), '..', 'schema.yaml')
    with open(schema_file, 'rb') as fh:
        data = yaml.load(fh)
        return data


def load_schema(data):
    name = data.get('name')
    try:
        schema = grano.schemata.by_name(name)
        schema._data = data
        schema.save()
        log.info('Updated schema: %s', schema.label)
    except NotFound:
        schema = grano.schemata.create(data)
        log.info('Created schema: %s', schema.label)


def load():
    for schema in load_file():
        load_schema(schema)
