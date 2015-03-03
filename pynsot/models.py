# -*- coding: utf-8 -*-

"""
Model classes to represent API dict results as objects in an ORM style.

See the examples in the docstring for ``ApiModel``.
"""

__author__ = 'Jathan McCollum'
__maintainer__ = 'Jathan McCollum'
__email__ = 'jathan@dropbox.com'
__copyright__ = 'Copyright (c) 2015 Dropbox, Inc.'


import collections


# Valid top-level types.
TYPES = ('network', 'attribute', 'user', 'site', 'device')


# What an error response looks like:
'''
{
    "status": "error",
    "error": {
        "code": 404,
        "message": "Resource not found."
    }
}
'''


class ApiModel(collections.MutableMapping):
    """
    Simple class to make an API response dict into an object.

    For example, for a site object::

        >>> site1 = api.sites(1).get()
        >>> site1
        {u'data': {u'site': {u'description': u'Foo site', u'id': 1, u'name':
         u'Foo'}},
         u'status': u'ok'}
        >>> site_obj = ApiModel(site1)
        >>> site_obj
        <Site(id=1, name=u'Foo', description=u'Foo site')>
        >>> site_obj.name
        u'Foo'

    Network object::

        >>> site = api.sites(1).get()
        >>> nw1 = site.networks(1).get()
        >>> nw1 = api.sites(1).networks(1).get()
        {u'data': {u'network': {u'attributes': {},
           u'id': 1,
           u'ip_version': u'4',
           u'is_ip': False,
           u'network_address': u'10.0.0.0',
           u'parent_id': None,
           u'prefix_length': 8,
           u'site_id': 1}},
         u'status': u'ok'}
        >>> nw_obj = ApiModel(nw1)
        >>> nw_obj
        <Network(is_ip=False, network_address=u'10.0.0.0', site_id=1,
         parent_id=None, prefix_length=8, ip_version=u'4', attributes={},
         id=1)>
        >>> nw_obj.network_address
        u'10.0.0.0'
    """
    def __init__(self, data, **kwargs):
        if 'data' not in data:
            raise SyntaxError("Data must contain a 'data' field.")
        obj = data['data']

        if len(obj) > 1:
            raise SyntaxError('More than one object type found.')
        obj_type = obj.keys()[0]

        if obj_type not in TYPES:
            raise SyntaxError('Invalid type: %s' % (obj_type,))

        self._object_type = obj_type
        obj_data = obj[obj_type]
        self.__dict__.update(obj_data)

    def _repr_name(self):
        """Normalize object type to display in repr."""
        cls_name = self._object_type.title().replace('_', '')
        return cls_name

    def __repr__(self):
        cls_name = self._repr_name()
        attrs = ', '.join('%s=%r' % (k, v) for k, v in self.items())
        return '<%s(%s)>' % (cls_name, attrs)

    # collections.MutableMapping requires these to be defined to dictate the
    # dictionary-like behavior.

    def __getitem__(self, val):
        return self.__dict__[val]

    def __setitem__(self, key, val):
        self.__dict__[key] = val

    def __delitem__(self, key):
        del self.__dict__[key]

    def __iter__(self):
        return iter(k for k in self.__dict__ if not k.startswith('_'))

    def __len__(self):
        return len(self.__dict__)
