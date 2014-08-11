from connectedafrica.core import schemata


PROPERTIES_TABLE_IGNORE = ['name', 'tagline', 'summary']


class Property(object):

    def __init__(self, prop, attr):
        self.name = attr.get('name')
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
            val = val.strftime('%Y')
        return val


class Properties(object):

    def __init__(self, obj):
        self.obj = obj
        self.attributes = schemata.attributes(obj)

    @property
    def properties(self):
        for name, data in self.obj.properties.items():
            yield Property(data, self.attributes.get(name))

    def __getattr__(self, name):
        for prop in self.properties:
            if prop.name == name:
                return prop
        return None

    def __iter__(self):
        for prop in self.properties:
            if not prop.hidden:
                yield prop
