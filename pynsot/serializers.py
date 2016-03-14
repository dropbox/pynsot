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

from __future__ import unicode_literals

from .vendor.slumber.serialize import JsonSerializer
from .import models


__author__ = 'Jathan McCollum'
__maintainer__ = 'Jathan McCollum'
__email__ = 'jathan@dropbox.com'
__copyright__ = 'Copyright (c) 2015-2016 Dropbox, Inc.'


class ModelSerializer(JsonSerializer):
    """This serializes to a model instead of a dict."""
    key = 'model'

    def get_serializer(self, *args, **kwargs):
        return self

    def loads(self, data):
        obj_data = super(ModelSerializer, self).loads(data)
        return models.ApiModel(obj_data)
