# -*- coding: utf-8 -*-

"""
Test the Models
"""

from __future__ import unicode_literals
import pytest

from pytest import raises

from pynsot.models import Resource, Network, Device, Interface
from pynsot.util import get_result
from .fixtures import config, client, site

__all__ = ('client', 'config', 'pytest', 'site')


def test_fail_abc(client):
    '''Test that abc is doing its job'''
    class A(Resource):
        pass

    with raises(TypeError):
        a = A(client=client, site_id=1)
        return a


def test_correct_site(client, site):
    '''Tests that a resource gets sent to the correct site_id'''
    n = Network(client=client, site_id=site['id'], cidr='8.8.8.0/24')
    assert n.ensure()
    assert n.existing_resource()['site_id'] == site['id']

    from pynsot.util import get_result
    manual = get_result(client.sites(site['id']).networks('8.8.8.0/24').get())
    assert manual['site_id'] == site['id']


def test_args(client, site):
    '''Tests for exceptions that should be thrown in certain arg combos'''
    with raises(TypeError):
        # not including cidr or raw
        Network(client=client, site=site['id'])
    with raises(TypeError):
        # including raw, but not raw['site_id']
        Network(client=client, raw={})
    with raises(TypeError):
        # not including hostname or raw
        Device(client=client, site=site['id'])
    with raises(TypeError):
        # not including name+device or raw
        Interface(client=client, site=site['id'])


def test_raw_precedence(client, site):
    '''Makes sure raw kwarg site_id takes precedence'''
    # first create a resource to get raw from
    n = Network(client=client, site_id=site['id'], cidr='8.8.8.0/24')
    assert n.ensure()

    # Make sure that raw settings take precedence
    raw = n.existing_resource()
    n2 = Network(client=client, site=999, raw=raw)
    assert n2['site_id'] != 999


def test_existing(client, site):
    '''Test functionality around existing resource and caching of the result'''
    site_id = site['id']
    c = client

    n = Network(client=c, site_id=site_id, cidr='8.8.8.0/24')
    assert n.purge()
    assert not n.exists()
    assert n._existing_resource == {}
    assert n.existing_resource() == n._existing_resource
    assert n.ensure()
    # Make sure cache clearing works
    assert n._existing_resource == {}
    assert n.exists()
    assert n.existing_resource() == n._existing_resource


def test_net_closest_parent(client, site):
    '''Test that Network.closest_parent returns instance of Network or dict'''
    site_id = site['id']
    c = client

    parent = Network(client=c, site_id=site_id, cidr='8.8.8.0/24')
    assert parent.ensure()

    child = Network(client=c, site_id=site_id, cidr='8.8.8.8/32')
    assert child.closest_parent() == parent

    orphan = Network(client=c, site_id=site_id, cidr='1.1.1.1/32')
    assert not orphan.closest_parent()
    assert orphan.closest_parent() == {}


def test_dict():
    '''Test methods/behavior that should work like a dictionary'''
    n = Network(site_id=1, cidr='8.8.8.0/24')
    assert n['site_id'] == 1
    n['site_id'] = 2
    assert n['site_id'] == 2

    assert n.keys()
    assert n.items()
    assert dict(n)


def test_payload_not_none_raw_and_not(client, site):
    '''Make sure payload gets set fine for both EZ and raw approaches

    Also make sure both instances are the same, using comparisons
    '''
    n = Network(client=client, site_id=site['id'], cidr='8.8.8.0/24')
    assert n.payload
    assert n.ensure()

    n2 = Network(
        raw=get_result(
            client.sites(site['id']).networks('8.8.8.0/24').get()
        )
    )

    assert n2.payload

    # Test some magic methods on raw-init'd instance
    assert len(n2)
    assert n == n2
    assert n2.keys()
    assert n2.items()


def test_clear_cache_on_change(client, site):
    '''Test that cache is cleared on any change to the instance'''
    site_id = site['id']
    c = client

    n = Network(client=c, site_id=site_id, cidr='8.8.8.0/24')
    assert n.ensure()
    assert n.exists()

    non_existing_site = get_result(c.sites.get())[-1]['id'] + 1000
    n['site_id'] = non_existing_site
    # First assert that the cache property was cleared
    assert not n._existing_resource
    assert not n.existing_resource()
    # assert that the resource isn't successfully looked up if site doesn't
    # match
    assert not n.exists()
    # Change site back and test
    n['site_id'] = site_id
    assert n.exists()


def test_ip4_host():
    '''Test to make sure IPv4 host works fine'''
    net = '8.8.8.8/32'
    n = Network(site_id=1, cidr=net)
    assert n['network_address'] == '8.8.8.8'
    assert n['prefix_length'] == 32
    assert n.identifier == net
    assert n['site_id'] == 1
    assert n.is_host
    assert n.resource_name == 'networks'
    assert n['state'] == 'assigned'
    assert dict(n)
    assert n['attributes'] == {}
    assert n['network_address']


def test_ip4_net(client):
    '''Test to make sure IPv4 subnet works fine'''
    net = '8.8.8.0/24'
    n = Network(client=client, site_id=1, cidr=net)
    assert n['network_address'] == '8.8.8.0'
    assert n['prefix_length'] == 24
    assert n.identifier == net
    assert n['site_id'] == 1
    assert not n.is_host
    assert n.resource_name == 'networks'
    assert n['state'] == 'allocated'
    assert dict(n)
    assert n['network_address']


def test_ip6_net(client):
    '''Test to make sure IPv6 subnet works fine'''
    net = '2001::/64'
    n = Network(client=client, site_id=1, cidr=net)
    assert n['network_address'] == '2001::'
    assert n['prefix_length'] == 64
    assert n.identifier == net
    assert n['site_id'] == 1
    assert not n.is_host
    assert n.resource_name == 'networks'
    assert n['state'] == 'allocated'
    assert dict(n)
    assert n['network_address']


def test_ip6_host(client):
    '''Test to make sure IPv6 host works fine'''
    net = '2001::1/128'
    n = Network(client=client, site_id=1, cidr=net)
    assert n['network_address'] == '2001::1'
    assert n['prefix_length'] == 128
    assert n.identifier == net
    assert n['site_id'] == 1
    assert n.is_host
    assert n.resource_name == 'networks'
    assert n['state'] == 'assigned'
    assert dict(n)
    assert n['network_address']


def test_device(client):
    '''Test to make sure device works fine'''
    name = 'pytest'
    d = Device(client=client, site_id=1, hostname=name)
    assert d['hostname'] == name
    assert d.identifier == name
    assert d['site_id'] == 1
    assert d.resource_name == 'devices'
    assert dict(d)
    assert d['hostname']
    assert d['attributes'] == {}
    d['attributes'] = {'desc': 'test host'}


def test_device_eq(client):
    '''Test to make sure device comparison works fine'''
    name = 'pytest'
    d1 = Device(client=client, site_id=1, hostname=name)
    d2 = Device(client=client, site_id=1, hostname=name)
    assert d1 == d2


def test_interface(client):
    '''Test to make sure interface init works fine'''
    name = 'eth0'
    i = Interface(client=client, site_id=1, name=name, device=1)
    assert i['name'] == name
    assert i['device'] == 1
    assert i['site_id'] == 1
    assert i.resource_name == 'interfaces'
    assert dict(i)
    assert i['name']
    assert i['attributes'] == {}
    i['attributes'] = {'desc': 'test host'}


def test_interface_eq(client):
    '''Test to make sure interface comparison works fine'''
    name = 'eth0'
    i1 = Interface(client=client, site_id=1, name=name, device=1)
    i2 = Interface(client=client, site_id=1, name=name, device=1)
    assert i1 == i2


def test_ip4_send(client, site):
    '''Test upstream write actions for IPv4'''

    site_id = site['id']
    subnet = Network(client=client, site_id=site_id, cidr='254.0.0.0/24')
    host = Network(client=client, site_id=site_id, cidr='254.0.0.1/32')

    assert subnet.purge()
    assert not subnet.exists()
    assert subnet.ensure()
    assert subnet.exists()
    assert host.purge()
    assert not host.exists()
    assert host.ensure()
    assert host.exists()

    host.purge()
    subnet.purge()
    assert not all([subnet.exists(), host.exists()])


def test_device_send(client, site):
    '''Test upstream write actions for devices'''
    site_id = site['id']
    name = 'pytest'
    d = Device(client=client, site_id=site_id, hostname=name)
    assert d.purge()
    assert not d.exists()
    assert d.ensure()
    assert d.exists()
    assert d.purge()
    assert not d.exists()


# This section is commented out because some changes need make to interfaces to
# better support friendly-specifying hostname vs. device ID during
# instantiation.
#
# def test_interface_send(client, site):
#    '''Test upstream write actions for interfaces'''
#     site_id = site['id']
#     host = 'intftest'
#     d = Device(client=client, site_id=site_id, hostname=host)
#     assert d.ensure()
#
#     i = Interface(client=client, site_id=site_id, name='eth0', device=host)
#
#     assert i.purge()
#     assert not i.exists()
#     assert i.ensure()
#     assert i.exists()
#     assert i.purge()
#     assert not i.exists()
#
#     assert d.purge()
#     assert not d.exists()
#
#
# def test_interface_wo_device(client, site):
#    '''Test to make sure device is set to 0 if doesnt exist'''
#     site_id = site['id']
#     host = 'doesnt-exist-yet'
#     d = Device(client=client, site_id=site_id, hostname=host)
#     assert d.purge()
#
#     i = Interface(client=client, site_id=site_id, name='eth0', device=host)
#     assert i
#     assert i['device'] == 0
#
#     assert d.ensure()
#
#     # The device id is checked every time __iter__ is called
#     assert i['device'] != 0
#
#     d.purge()
