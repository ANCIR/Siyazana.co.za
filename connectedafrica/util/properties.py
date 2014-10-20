from datetime import datetime

from connectedafrica.core import schemata


PROPERTIES_TABLE_IGNORE = ['name', 'tagline', 'summary']
DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'


class Property(object):

    def __init__(self, prop, attr):
        self.name = attr.get('name')
        self.source_url = prop.get('source_url')
        self.label = attr.get('label', attr.get('name'))
        self.prop = prop
        self.attr = attr

    @property
    def hidden(self):
        return self.attr.get('hidden') \
            or self.attr.get('name') in PROPERTIES_TABLE_IGNORE

    @property
    def value(self):
        val = self.prop.get('value')
        typ = self.attr.get('datatype')
        if typ == 'datetime':
            val = datetime.strptime(val, DATETIME_FORMAT)
        return val

    def __unicode__(self):
        return unicode(self.value)


class Properties(object):

    def __init__(self, obj):
        self.obj = obj
        self.attributes = schemata.attributes(obj)

    @property
    def properties(self):
        for name, data in self.obj.properties.items():
            yield Property(data, self.attributes.get(name))

    def __getattr__(self, name):
        return self.get(name)

    def get(self, name):
        for prop in self.properties:
            if prop.name == name:
                return prop
        return None

    def __contains__(self, name):
        for prop in self.properties:
            if prop.name == name:
                return True
        return False

    def __iter__(self):
        for prop in self.properties:
            if not prop.hidden:
                yield prop
