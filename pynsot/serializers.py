# -*- coding: utf-8 -*-

"""
Specialized serializers for NSoT API client.

This is an example of how you would use this with the Client object, to make it
return objects instead of dicts::

    >>> serializer = ModelSerializer()
    >>> api = Client(url, serializer=serializer)
    >>> obj = api.sites(1).get()
    >>> obj
    <Site(id=1, description=u'Foo site', name=u'Foo')>
"""

__author__ = 'Jathan McCollum'
__maintainer__ = 'Jathan McCollum'
__email__ = 'jathan@dropbox.com'
__copyright__ = 'Copyright (c) 2015 Dropbox, Inc.'


import models

from .vendor.slumber.serialize import JsonSerializer


class ModelSerializer(JsonSerializer):
    """This serializes to a model instead of a dict."""
    key = 'model'

    def get_serializer(self, *args, **kwargs):
        return self

    def loads(self, data):
        obj_data = super(ModelSerializer, self).loads(data)
        return models.ApiModel(obj_data)
