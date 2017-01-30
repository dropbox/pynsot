# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import pytest

from tests.fixtures import site_client


@pytest.fixture
def circuit_attributes(site_client):
    attr_names = [
        'owner',
        'vendor'
    ]

    attrs = ({'name': a, 'resource_name': 'Circuit'} for a in attr_names)
    client = site_client.sites(site_client.default_site).attributes
    return map(client.post, attrs)


@pytest.fixture
def device_a(site_client):
    """ Device for the A side of the circuit """

    return site_client.sites(site_client.default_site).devices.post(
        {'hostname': 'foo-bar01'}
    )


@pytest.fixture
def device_z(site_client):
    """ Device for the Z side of the circuit """

    return site_client.sites(site_client.default_site).devices.post(
        {'hostname': 'foo-bar02'}
    )


@pytest.fixture
def interface_a(site_client, device_a, network):
    """ Interface for the A side of the circuit """

    return site_client.sites(site_client.default_site).interfaces.post({
        'device': device_a['id'],
        'name': 'eth0',
        'addresses': ['10.20.30.2/32'],
    })


@pytest.fixture
def interface_z(site_client, device_z, network):
    """ Interface for the Z side of the circuit """

    return site_client.sites(site_client.default_site).interfaces.post({
        'device': device_z['id'],
        'name': 'eth0',
        'addresses': ['10.20.30.3/32'],
    })


@pytest.fixture
def circuit(site_client, circuit_attributes, interface_a, interface_z):
    """ Circuit connecting interface_a to interface_z """

    return site_client.sites(site_client.default_site).circuits.post({
        'name': 'test_circuit',
        'endpoint_a': interface_a['id'],
        'endpoint_z': interface_z['id'],
        'attributes': {
            'owner': 'alice',
            'vendor': 'lasers go pew pew',
        },
    })


@pytest.fixture
def dangling_circuit(site_client, interface):
    """
    Circuit where we only own the local site, remote (Z) end is a vendor
    """

    return site_client.sites(site_client.default_site).circuits.post({
        'name': 'remote_vendor_circuit',
        'endpoint_a': interface['id'],
    })
