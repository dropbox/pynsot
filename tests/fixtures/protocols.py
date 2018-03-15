# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import pytest

from tests.fixtures import (protocol_type, site_client)

from .circuits import (circuit, device_a, interface_a)

@pytest.fixture
def protocol(site_client, device_a, interface_a, circuit, protocol_type):
    """
    Return a Protocol Object.
    """
    device_id = device_a['id']
    interface_slug = '{device_hostname}:{name}'.format(**interface_a)
    return site_client.sites(site_client.default_site).protocols.post(
        {
            'device': device_id,
            'type': 'bgp',
            'interface': interface_slug,
            'attributes': {'foo': 'test_protocol'},
            'circuit': circuit['name'],
            'description': 'bgp is the best',
        }
    )

@pytest.fixture
def protocol_attribute(site_client, protocol):
    return site_client.sites(site_client.default_site).attributes.post(
        {
            'name':'boo',
            'value': 'test_attribute',
            'resource_name': 'Protocol',
        }
    )
