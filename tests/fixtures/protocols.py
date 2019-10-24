# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import pytest

from tests.fixtures import (protocol_type, site_client)

from .circuits import (circuit, device_a, interface_a)
from six.moves import range

@pytest.fixture
def protocol(site_client, device_a, interface_a, circuit, protocol_type):
    """
    Return a Protocol Object.
    """
    device_id = device_a['id']
    interface_slug = interface_a['name_slug']
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
def protocol_attribute(site_client):
    return site_client.sites(site_client.default_site).attributes.post(
        {
            'name':'boo',
            'value': 'test_attribute',
            'resource_name': 'Protocol',
        }
    )

@pytest.fixture
def protocol_attribute2(site_client):
    return site_client.sites(site_client.default_site).attributes.post(
        {
            'name':'foo',
            'value': 'test_protocol',
            'resource_name': 'Protocol',
        }
    )


@pytest.fixture
def protocols(site_client, protocol_type, protocol_attribute2):
    """
    A group of Protocol objects for testing limit/offest/etc.
    """
    protocols = []
    site = site_client.sites(site_client.default_site)
    for i in range(1, 6):
        device_name = 'device{:02d}'.format(i)
        interface_name = 'Ethernet1/{}'.format(i)

        device = site.devices.post({'hostname': device_name})
        interface = site.interfaces.post({
            'device': device['id'],
            'name': interface_name,
        })

        protocol = site.protocols.post({
            'type': protocol_type['name'],
            'device': device['id'],
            'interface': interface['id'],
            'attributes': {'foo': 'bar'},
        })
        protocols.append(protocol)

    return protocols
