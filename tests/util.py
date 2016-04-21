# -*- coding: utf-8 -*-

"""
Utilities for testing.
"""

from __future__ import unicode_literals
import collections
import contextlib
from itertools import islice
import logging
import os
import random
import shlex
import shutil
import socket
import struct
import tempfile

from pynsot.app import app
from pynsot import client
from pynsot import dotfile
from pynsot.vendor.click.testing import CliRunner as BaseCliRunner


log = logging.getLogger(__name__)

# Phony attributes to randomly generate for testing.
ATTRIBUTE_DATA = {
    'lifecycle': ['monitored', 'ignored'],
    'owner': ['jathan', 'gary', 'lisa', 'jimmy', 'bart', 'bob', 'alice'],
    'metro': ['lax', 'iad', 'sjc', 'tyo'],
    'foo': ['bar', 'baz', 'spam'],
}

# Used to store Attribute/value pairs
Attribute = collections.namedtuple('Attribute', 'name value')

# Hard-code the app name as 'nsot' to match the CLI util.
app.name = 'nsot'


class CliRunner(BaseCliRunner):
    """
    Subclass of CliRunner that also creates a .pynsotrc in the isolated
    filesystem.
    """
    def __init__(self, client_config, *args, **kwargs):
        self.client_config = client_config
        super(CliRunner, self).__init__(*args, **kwargs)

    @contextlib.contextmanager
    def isolated_filesystem(self):
        """
        A context manager that creates a temporary folder and changes
        the current working directory to it for isolated filesystem tests.
        """
        # If user config is found, back it up for duration of each test.
        config_path = os.path.expanduser('~/.pynsotrc')
        backup_path = config_path + '.orig'
        backed_up = False
        if os.path.exists(config_path):
            log.debug('Config found, backing up...')
            os.rename(config_path, backup_path)
            backed_up = True

        cwd = os.getcwd()
        t = tempfile.mkdtemp()
        os.chdir(t)
        rcfile = dotfile.Dotfile('.pynsotrc')
        rcfile.write(self.client_config)
        try:
            yield t
        finally:
            os.chdir(cwd)
            if backed_up:
                log.debug('Restoring original config.')
                os.rename(backup_path, config_path)  # Restore original
            try:
                shutil.rmtree(t)
            except (OSError, IOError):
                pass

    def run(self, command, **kwargs):
        """
        Shortcut to invoke to parse command and pass app along.

        :param command:
            Command args e.g. 'devices list'

        :param kwargs:
            Extra keyword arguments to pass to ``invoke()``
        """
        cmd_parts = shlex.split(command)
        result = self.invoke(app, cmd_parts, **kwargs)
        return result


def assert_output(result, expected, exit_code=0):
    """
    Assert that output matches the conditions.

    :param result:
        CliRunner result object

    :param expected:
        List/tuple of expected outputs

    :param exit_code:
        Expected exit code
    """
    if not isinstance(expected, (tuple, list)):
        raise TypeError('Expected must be a list or tuple')

    assert result.exit_code == exit_code
    output = result.output.splitlines()

    for line in output:
        # Assert that the expected items are found on the same line
        if not all((e in line) for e in expected):
            continue
        else:
            log.info('matched: %r', (expected,))
            break
    else:
        assert False


def assert_outputs(result, expected_list, exit_code=0):
    """
    Assert output over a list of of lists of expected outputs.

    :param result:
        CliRunner result object

    :param expected_list:
        List of lists/tuples of expected outputs

    :param exit_code:
        Expected exit code
    """
    for expected in expected_list:
        assert_output(result, expected, exit_code)


def rando():
    """Flip a coin."""
    return random.choice((True, False))


def take_n(n, iterable):
    "Return first n items of the iterable as a list"
    return list(islice(iterable, n))


def generate_hostnames(num_items=100):
    """
    Generate a random list of hostnames.

    :param num_items:
        Number of items to generate
    """

    for i in range(1, num_items + 1):
        yield 'host%s' % i


def generate_ipv4():
    """Generate a random IPv4 address."""
    return socket.inet_ntoa(struct.pack('>I', random.randint(1, 0xffffffff)))


def generate_ipv4list(num_items=100, include_hosts=False):
    """
    Generate a list of unique IPv4 addresses. This is a total hack.

    :param num_items:
        Number of items to generate

    :param include_hosts:
        Whether to include /32 addresses
    """
    ipset = set()
    # Keep iterating and hack together cidr prefixes if we detect empty
    # trailing octects. This is so lame that we'll mostly just end up with a
    # bunch of /24 networks.
    while len(ipset) < num_items:
        ip = generate_ipv4()
        if ip.startswith('0'):
            continue

        if ip.endswith('.0.0.0'):
            prefix = '/8'
        elif ip.endswith('.0.0'):
            prefix = '/16'
        elif ip.endswith('.0'):
            prefix = '/24'
        elif include_hosts:
            prefix = '/32'
        else:
            continue

        ip += prefix
        ipset.add(ip)

    return sorted(ipset)


def enumerate_attributes(resource_name, attributes=None):
    if attributes is None:
        attributes = ATTRIBUTE_DATA

    for name in attributes:
        yield {'name': name, 'resource_name': resource_name}


def generate_attributes(attributes=None, as_dict=True):
    """
    Randomly choose attributes and values for testing.

    :param attributes:
        Dictionary of attribute names and values

    :param as_dict:
        If set return a dict vs. list of Attribute objects
    """
    if attributes is None:
        attributes = ATTRIBUTE_DATA

    attrs = []
    for attr_name, attr_values in attributes.iteritems():
        if random.choice((True, False)):
            attr_value = random.choice(attr_values)
            attrs.append(Attribute(attr_name, attr_value))

    if as_dict:
        attrs = dict(attrs)

    return attrs


def generate_devices(num_items=100, with_attributes=True):
    """
    Return a list of dicts for Device creation.

    :param num_items:
        Number of items to generate

    :param with_attributes:
        Whether to include Attributes
    """
    hostnames = generate_hostnames(num_items)

    devices = []
    for hostname in hostnames:
        item = {'hostname': hostname}
        if with_attributes:
            item['attributes'] = generate_attributes()

        devices.append(item)

    return devices


def generate_interface(name, device_id=None, with_attributes=True,
                       addresses=None):
    """
    Return a list of dicts for Interface creation.

    :param device_id:
        The device_id for the Interface

    :param with_attributes:
        Whether to include Attributes

    :param addresses:
        List of addresses to assign to the Interface
    """
    speeds = (100, 1000, 10000, 40000)
    types = (6, 135, 136, 161)
    if addresses is None:
        addresses = []

    item = {
        'name': name,
        # 'device_id': device_id,
        'device': device_id,
        'speed': random.choice(speeds),
        'type': random.choice(types),
    }

    if with_attributes:
        item['attributes'] = generate_attributes()
    if addresses:
        item['addresses'] = addresses

    return item


def generate_interfaces(device_id=None, with_attributes=True,
                        address_pool=None):
    """
    Return a list of dicts for Interface creation.

    Will generate as many Interfaces as there are in the address_pool.

    :param device_id:
        The device_id for the Interface

    :param num_items:
        Number of items to generate

    :param with_attributes:
        Whether to include Attributes

    :param address_pool:
        Pool of addresses to assign
    """
    prefix = 'eth'

    if address_pool is None:
        address_pool = []

    interfaces = []
    for num, address in enumerate(address_pool):
        name = prefix + str(num)

        # Currently hard-coded to 1 address per interface.
        addresses = [address]

        item = generate_interface(
            name, device_id, with_attributes=with_attributes,
            addresses=addresses
        )
        interfaces.append(item)

    return interfaces


def generate_networks(num_items=100, with_attributes=True, include_hosts=False,
                      ipv4list=None):
    """
    Return a list of dicts for Network creation.

    :param num_items:
        Number of items to generate

    :param with_attributes:
        Whether to include Attributes
    """
    if ipv4list is None:
        ipv4list = generate_ipv4list(num_items, include_hosts=include_hosts)

    networks = []
    for cidr in ipv4list:
        item = {'cidr': str(cidr)}
        if with_attributes:
            item['attributes'] = generate_attributes()

        networks.append(item)

    return networks


def populate_sites(site_data):
    """Populate sites from fixture data."""
    api = client.Client('http://localhost:8990/api', email='jathan@localhost')

    results = []
    for d in site_data:
        try:
            result = api.sites.post(d)
        except Exception as err:
            print err, d['name']
        else:
            results.append(result)

    print 'Created', len(results), 'sites.'


def rando_set_action():
    """Return a random set theory query action."""
    return random.choice(['+', '-', ''])


def rando_set_query():
    """Return a random set theory query string."""
    action = rando_set_action()
    return ' '.join(
        action + '%s=%s' % (k, v) for k, v in generate_attributes().iteritems()
    )
