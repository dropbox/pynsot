#!/usr/bin/env python
from __future__ import unicode_literals

"""
Generate fixtures for NSoT dev/testing.
"""

import netaddr

# from . import util as fx
import util as fx
from pynsot import client


# API_URL = 'http://localhost:8990/api'
API_URL = 'http://localhost:8000/api'
# API_URL = 'http://localhost:80/api'
EMAIL = 'admin@localhost'

api = client.EmailHeaderClient(API_URL, email=EMAIL)
site_obj = api.sites.post({'name': 'Test Site'})['data']['site']
site = api.sites(site_obj['id'])


##############
# Attributes #
##############

# Populate attributes
resource_names = ('Device', 'Network', 'Interface')
attributes = []
for resource_name in resource_names:
    attrs = fx.enumerate_attributes(resource_name)
    attributes.extend(attrs)

# Create Attribute objects
site.attributes.post(attributes)
print 'Populated Attributes.'


############
# Networks #
############

# What's our supernet to derive from?
supernet = netaddr.IPNetwork('10.16.32.0/20')  # 16x /24
# supernet = netaddr.IPNetwork('10.16.32.0/23')  # 2x /24

# Populate the /20
parents = fx.generate_networks(ipv4list=[str(supernet)])

# Populate the /24s
networks = fx.generate_networks(ipv4list=(str(n) for n in supernet.subnet(24)))

# Populate the /32s
addresses = []
for net in supernet.subnet(24):
    hosts = (str(h) for h in net.iter_hosts())
    addresses.extend(fx.generate_networks(ipv4list=hosts))

# Create Network objects
for items in (parents, networks, addresses):
    site.networks.post(items)
print 'Populated Networks.'


###########
# Devices #
###########
# 16 hosts per /24
devices = fx.generate_devices(16 * len(networks))

# Create Device objects
site.devices.post(devices)
print 'Populated Devices.'


##############
# Interfaces #
##############
# Get list of device ids
dev_resp = site.devices.get()
device_ids = [dev['id'] for dev in dev_resp['data']['devices']]

# Get list of IP addreses and make them an iterable for take()
ip_list = [a['cidr'] for a in addresses]
ip_iter = iter(ip_list)

# 16 interfaces per host
interfaces = []
for device_id in device_ids:
    my_ips = fx.take_n(16, ip_iter)
    my_interfaces = fx.generate_interfaces(device_id, address_pool=my_ips)
    interfaces.extend(my_interfaces)

# Create Interface objects
site.interfaces.post(interfaces)
print 'Populated Interfaces.'
