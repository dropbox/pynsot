# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""
Test the CLI app.
"""

import contextlib
import copy
import logging
import os
import pytest
import re
import requests_mock
import shlex
import shutil
import tempfile

from pynsot import dotfile
from pynsot.app import app
from pynsot.vendor import click
from pynsot.vendor.click.testing import CliRunner as BaseCliRunner

from .fixtures import (
    config, AUTH_RESPONSE, API_URL, DEVICES_RESPONSE, ATTRIBUTES_RESPONSE,
    DEVICE_RETRIEVE, DEVICE_UPDATE, NETWORK_CREATE, NETWORK_RETRIEVE,
    NETWORK_UPDATE, NETWORKS_RESPONSE
)


log = logging.getLogger(__name__)

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
        """A context manager that creates a temporary folder and changes
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


#########
# Sites #
#########
def test_site_id(config):
    """Test ``nsot devices list`` without required site_id"""
    headers = {'Content-Type': 'application/json'}
    auth_url = config['url'] + '/authenticate/'
    devices_url = config['url'] + '/sites/1/devices/'

    runner = CliRunner(config)
    with requests_mock.Mocker() as mock, runner.isolated_filesystem():
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.get(devices_url, json=DEVICES_RESPONSE, headers=headers)

        result = runner.invoke(app, shlex.split('devices list'))

        # Make sure it says site-id is required
        assert result.exit_code == 2
        expected_output = (
            'Usage: nsot devices list [OPTIONS]\n'
            '\n'
            'Error: Missing option "-s" / "--site-id".\n'
        )
        assert result.output == expected_output


def test_site_add(config):
    """Test addition of a site."""
    headers = {'Content-Type': 'application/json'}
    auth_url = config['url'] + '/authenticate/'
    sites_url = config['url'] + '/sites/'
    site_uri = config['url'] + '/sites/1/'

    SITE_RESPONSE = {
        'data': {
            'site': {'description': 'Foo site.', 'id': 1, 'name': 'Foo'}
        },
        'status': 'ok'
    }
    ERROR_RESPONSE = {
        'status': 'error',
        'error': {
            'message': {'name': ['This field must be unique.']},
            'code': 400
         }
    }

    runner = CliRunner(config)
    with requests_mock.Mocker() as mock, runner.isolated_filesystem():
        # Create the site
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.post(sites_url, json=SITE_RESPONSE, headers=headers)

        result = runner.invoke(
            app, shlex.split("sites add -n Foo -d 'Foo site.'")
        )
        assert result.exit_code == 0

        expected_output = (
            "[SUCCESS] Added site with args: name=Foo, description=Foo site.!\n"
        )
        assert result.output == expected_output

        # Try to create the site again!! And fail!!
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.post(sites_url, json=ERROR_RESPONSE, headers=headers,
                  status_code=400)

        result = runner.invoke(
            app, shlex.split("sites add -n Foo -d 'Foo site.'"),
            color=False
        )
        assert result.exit_code != 0
        assert result.output == ''


###########
# Devices #
###########
def test_device_add(config):
    """Test ``nsot devices add -s 1 -H foo-bar1``"""
    headers = {'Content-Type': 'application/json'}
    auth_url = config['url'] + '/authenticate/'
    devices_url = config['url'] + '/sites/1/devices/'

    runner = CliRunner(config)
    with requests_mock.Mocker() as mock, runner.isolated_filesystem():
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.post(devices_url, json=DEVICE_RETRIEVE, headers=headers)

        result = runner.invoke(app, shlex.split('devices add -s 1 -H foo-bar1'))
        assert result.exit_code == 0

        expected_output = (
            '[SUCCESS] Added device with args: bulk_add=None, attributes={}, '
            'hostname=foo-bar1!\n'
        )
        assert result.output == expected_output


def test_devices_bulk_add(config):
    """Test ``nsot devices add -s 1 -b /tmp/devices``"""
    headers = {'Content-Type': 'application/json'}
    auth_url = config['url'] + '/authenticate/'
    devices_url = config['url'] + '/sites/1/devices/'

    BULK_ADD = (
        'hostname:attributes\n'
        'foo-bar1:owner=jathan\n'
        'foo-bar2:owner=jathan\n'
    )
    BULK_FAIL = (
        'hostname:attributes\n'
        'foo-bar1:owner=jathan,bacon=delicious\n'
        'foo-bar2:owner=jathan\n'
    )
    BULK_ERROR = {
        'status': 'error',
        'error': {
            'code': 400,
            'message': 'Attribute name (bacon) does not exist.'
        }
    }

    runner = CliRunner(config)
    with requests_mock.Mocker() as mock, runner.isolated_filesystem():
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.post(devices_url, json=DEVICES_RESPONSE, headers=headers)

        # Write the bulk file.
        with open('bulk_file', 'w') as fh:
            fh.writelines(BULK_ADD)

        # Test *with* provided site_id
        result = runner.invoke(
            app, shlex.split('devices add -s 1 -b bulk_file')
        )
        assert result.exit_code == 0

        expected_output = (
            "[SUCCESS] Added device with args: attributes={'owner': 'jathan'}, "
            "hostname=foo-bar1!\n"
            "[SUCCESS] Added device with args: attributes={'owner': 'jathan'}, "
            "hostname=foo-bar2!\n"
        )
        assert result.output == expected_output

        # Test an invalid add
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.post(devices_url, json=BULK_FAIL, headers=headers, status_code=400)

        with open('bulk_fail', 'w') as fh:
            fh.writelines(BULK_FAIL)

        result = runner.invoke(app, shlex.split('devices add -s 1 -b bulk_fail'))
        assert result.exit_code != 0

        # Test *without* provided site_id, but with default_site in a new
        # dotfile.
        rcfile = dotfile.Dotfile('.pynsotrc')
        config['default_site'] = '1'
        rcfile.write(config)

        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.post(devices_url, json=DEVICES_RESPONSE, headers=headers)

        result = runner.invoke(app, shlex.split('devices add -b bulk_file'))
        assert result.exit_code == 0
        assert result.output == expected_output


def test_devices_list(config):
    """Test ``nsot devices list -s 1``"""
    headers = {'Content-Type': 'application/json'}
    auth_url = config['url'] + '/authenticate/'
    devices_url = config['url'] + '/sites/1/devices/'

    runner = CliRunner(config)
    with requests_mock.Mocker() as mock, runner.isolated_filesystem():
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.get(devices_url, json=DEVICES_RESPONSE, headers=headers)

        # Normal list
        result = runner.invoke(app, shlex.split('devices list -s 1'))
        assert result.exit_code == 0

        expected_output = (
            '+------------------------------+\n'
            '| ID   Hostname   Attributes   |\n'
            '+------------------------------+\n'
            '| 1    foo-bar1   owner=jathan |\n'
            '| 2    foo-bar2   owner=jathan |\n'
            '+------------------------------+\n'
        )
        assert result.output == expected_output

        # Set query display newline-delimited (default)
        query_url = config['url'] + '/sites/1/devices/query/'
        mock.get(query_url, json=DEVICES_RESPONSE, headers=headers)
        result = runner.invoke(
            app, shlex.split('devices list -s 1 -q owner=jathan')
        )
        assert result.exit_code == 0

        expected_output = (
            'foo-bar1\n'
            'foo-bar2\n'
        )
        assert result.output == expected_output

        # Set query display comma-delimited (--delimited)
        result = runner.invoke(
            app, shlex.split('devices list -s 1 -q owner=jathan -d')
        )
        assert result.exit_code == 0

        expected_output = 'foo-bar1,foo-bar2\n'
        assert result.output == expected_output


def test_device_update(config):
    """Test ``nsot devices update -s 1 -i 1 -a monitored``"""
    headers = {'Content-Type': 'application/json'}
    auth_url = config['url'] + '/authenticate/'
    devices_url = config['url'] + '/sites/1/devices/'
    device_uri = config['url'] + '/sites/1/devices/1/'

    runner = CliRunner(config)
    with requests_mock.Mocker() as mock, runner.isolated_filesystem():
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.get(device_uri, json=DEVICE_RETRIEVE, headers=headers)
        mock.put(device_uri, json=DEVICE_UPDATE, headers=headers)

        # Run the update to add the new attribute
        result = runner.invoke(
            app,
            shlex.split('devices update -s 1 -i 1 -a monitored')
        )
        assert result.exit_code == 0

        expected_output = (
            "[SUCCESS] Updated device with args: attributes={'monitored':"
            " ''}, hostname=None!\n"
        )
        assert result.output == expected_output

        # Run a list to see the object w/ the updated result
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.get(device_uri, json=DEVICE_UPDATE, headers=headers)
        result = runner.invoke(
            app,
            shlex.split('devices list -s 1 -i 1')
        )
        assert result.exit_code == 0

        expected_output = (
            "+------------------------------+\n"
            "| ID   Hostname   Attributes   |\n"
            "+------------------------------+\n"
            "| 1    foo-bar1   owner=jathan |\n"
            "|                 monitored=   |\n"
            "+------------------------------+\n"
        )
        assert result.output == expected_output


##############
# Attributes #
##############
def test_attributes_list(config):
    """Test ``nsot attributes list -s 1``"""
    headers = {'Content-Type': 'application/json'}
    auth_url = config['url'] + '/authenticate/'
    devices_url = config['url'] + '/sites/1/attributes/'

    runner = CliRunner(config)
    with requests_mock.Mocker() as mock, runner.isolated_filesystem():
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.get(devices_url, json=ATTRIBUTES_RESPONSE, headers=headers)

        result = runner.invoke(app, shlex.split('attributes list -s 1'))
        assert result.exit_code == 0


############
# Networks #
############
def test_network_add(config):
    """Test ``nsot networks add -s 1 -c 10.0.0.0/8``"""
    headers = {'Content-Type': 'application/json'}
    auth_url = config['url'] + '/authenticate/'
    networks_url = config['url'] + '/sites/1/networks/'

    runner = CliRunner(config)
    with requests_mock.Mocker() as mock, runner.isolated_filesystem():
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.post(networks_url, json=NETWORK_CREATE, headers=headers)

        result = runner.invoke(app, shlex.split('networks add -s 1 -c 10.0.0.0/8'))
        assert result.exit_code == 0

        expected_output = (
            '[SUCCESS] Added network with args: bulk_add=None, attributes={}, '
            'cidr=10.0.0.0/8!\n'
        )
        assert result.output == expected_output


def test_networks_bulk_add(config):
    """Test ``nsot networks add -s 1 -b /tmp/networks``"""
    headers = {'Content-Type': 'application/json'}
    auth_url = config['url'] + '/authenticate/'
    networks_url = config['url'] + '/sites/1/networks/'

    BULK_ADD = (
        'cidr:attributes\n'
        '10.0.0.0/8:owner=jathan\n'
        '10.0.0.0/24:owner=jathan\n'
    )
    BULK_FAIL = (
        'cidr:attributes\n'
        '10.0.0.0/24:owner=jathan,bacon=delicious\n'
        '10.0.0.0/24:owner=jathan\n'
    )
    BULK_ERROR = {
        'status': 'error',
        'error': {
            'code': 400,
            'message': 'Attribute name (bacon) does not exist.'
        }
    }

    runner = CliRunner(config)
    with requests_mock.Mocker() as mock, runner.isolated_filesystem():
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.post(networks_url, json=NETWORKS_RESPONSE, headers=headers)

        # Write the bulk file.
        with open('bulk_file', 'w') as fh:
            fh.writelines(BULK_ADD)

        # Test *with* provided site_id
        result = runner.invoke(
            app, shlex.split('networks add -s 1 -b bulk_file')
        )
        assert result.exit_code == 0

        expected_output = (
            "[SUCCESS] Added network with args: attributes={'owner': 'jathan'}, "
            "cidr=10.0.0.0/8!\n"
            "[SUCCESS] Added network with args: attributes={'owner': 'jathan'}, "
            "cidr=10.0.0.0/24!\n"
        )
        assert result.output == expected_output

        # Test an invalid add
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.post(networks_url, json=BULK_FAIL, headers=headers, status_code=400)

        with open('bulk_fail', 'w') as fh:
            fh.writelines(BULK_FAIL)

        result = runner.invoke(app, shlex.split('networks add -s 1 -b bulk_fail'))
        assert result.exit_code != 0

        # Test *without* provided site_id, but with default_site in a new
        # dotfile.
        rcfile = dotfile.Dotfile('.pynsotrc')
        config['default_site'] = '1'
        rcfile.write(config)

        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.post(networks_url, json=NETWORKS_RESPONSE, headers=headers)

        result = runner.invoke(app, shlex.split('networks add -b bulk_file'))
        assert result.exit_code == 0
        assert result.output == expected_output


def test_networks_list(config):
    """Test ``nsot devices list -s 1``"""
    headers = {'Content-Type': 'application/json'}
    auth_url = config['url'] + '/authenticate/'
    networks_url = config['url'] + '/sites/1/networks/'

    runner = CliRunner(config)
    with requests_mock.Mocker() as mock, runner.isolated_filesystem():
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.get(networks_url, json=NETWORKS_RESPONSE, headers=headers)

        result = runner.invoke(app, shlex.split('networks list -s 1'))
        assert result.exit_code == 0

        expected_output = (
            '+----------------------------------------------------------------------+\n'
            '| ID   Network    Prefix   Is IP?   IP Ver.   Parent ID   Attributes   |\n'
            '+----------------------------------------------------------------------+\n'
            '| 1    10.0.0.0   8        False    4         None        owner=jathan |\n'
            '| 2    10.0.0.0   24       False    4         1           owner=jathan |\n'
            '+----------------------------------------------------------------------+\n'
        )
        assert result.output == expected_output

        # Set query display newline-delimited (default)
        query_url = config['url'] + '/sites/1/networks/query/'
        mock.get(query_url, json=NETWORKS_RESPONSE, headers=headers)
        result = runner.invoke(
            app, shlex.split('networks list -s 1 -q owner=jathan')
        )
        assert result.exit_code == 0

        expected_output = (
            '10.0.0.0/8\n'
            '10.0.0.0/24\n'
        )
        assert result.output == expected_output

        # Set query display comma-delimited (--delimited)
        result = runner.invoke(
            app, shlex.split('networks list -s 1 -q owner=jathan -d')
        )
        assert result.exit_code == 0

        expected_output = '10.0.0.0/8,10.0.0.0/24\n'
        assert result.output == expected_output


def test_network_subcommands(config):
    """Test supernets/subnets"""
    # Lookup subnets by cidr
    headers = {'Content-Type': 'application/json'}
    auth_url = config['url'] + '/authenticate/'
    networks_url = config['url'] + '/sites/1/networks/'
    network_match = re.compile(networks_url)

    SUBNETS = {
        'data': {
            'limit': None,
            'networks': [{'attributes': {'owner': 'jathan'},
            'id': 2,
            'ip_version': '4',
            'is_ip': False,
            'network_address': '10.0.0.0',
            'parent_id': 1,
            'prefix_length': 24,
            'site_id': 1}],
            'offset': 0,
            'total': 1},
         'status': 'ok'
    }
    SUPERNETS = {
        'data': {
            'limit': None,
            'networks': [
                {'attributes': {'owner': 'jathan'},
                'id': 1,
                'ip_version': '4',
                'is_ip': False,
                'network_address': '10.0.0.0',
                'parent_id': None,
                'prefix_length': 8,
                'site_id': 1}
            ],
            'offset': 0,
            'total': 1},
        'status': 'ok'
    }

    runner = CliRunner(config)
    with requests_mock.Mocker() as mock, runner.isolated_filesystem():
        # Test subnets
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.get(network_match, json=SUBNETS, headers=headers)

        result = runner.invoke(
            app, shlex.split('networks list -s 1 -c 10.0.0.0/8 subnets')
        )
        assert result.exit_code == 0

        expected_output = (
            '+----------------------------------------------------------------------+\n'
            '| ID   Network    Prefix   Is IP?   IP Ver.   Parent ID   Attributes   |\n'
            '+----------------------------------------------------------------------+\n'
            '| 2    10.0.0.0   24       False    4         1           owner=jathan |\n'
            '+----------------------------------------------------------------------+\n'
        )
        assert result.output == expected_output

        # Test supernets
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.get(network_match, json=SUPERNETS, headers=headers)

        result = runner.invoke(
            app, shlex.split('networks list -s 1 -c 10.0.0.0/24 supernets')
        )
        assert result.exit_code == 0

        expected_output = (
            '+----------------------------------------------------------------------+\n'
            '| ID   Network    Prefix   Is IP?   IP Ver.   Parent ID   Attributes   |\n'
            '+----------------------------------------------------------------------+\n'
            '| 1    10.0.0.0   8        False    4         None        owner=jathan |\n'
            '+----------------------------------------------------------------------+\n'
        )
        assert result.output == expected_output


def test_network_update(config):
    """Test ``nsot networks update -s 1 -i 1 -a foo=bar``"""
    headers = {'Content-Type': 'application/json'}
    auth_url = config['url'] + '/authenticate/'
    networks_url = config['url'] + '/sites/1/networks/'
    network_uri = config['url'] + '/sites/1/networks/1/'

    runner = CliRunner(config)
    with requests_mock.Mocker() as mock, runner.isolated_filesystem():
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.get(network_uri, json=NETWORK_RETRIEVE, headers=headers)
        mock.put(network_uri, json=NETWORK_UPDATE, headers=headers)

        # Run the update to add the new attribute
        result = runner.invoke(
            app,
            shlex.split('networks update -s 1 -i 1 -a foo=bar')
        )
        assert result.exit_code == 0

        expected_output = (
            "[SUCCESS] Updated network with args: attributes={'foo': 'bar'}!\n"
        )
        assert result.output == expected_output

        # Run a list to see the object w/ the updated result
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.get(network_uri, json=NETWORK_UPDATE, headers=headers)
        result = runner.invoke(
            app,
            shlex.split('networks list -s 1 -i 1')
        )
        assert result.exit_code == 0

        expected_output = (
            '+----------------------------------------------------------------------+\n'
            '| ID   Network    Prefix   Is IP?   IP Ver.   Parent ID   Attributes   |\n'
            '+----------------------------------------------------------------------+\n'
            '| 1    10.0.0.0   8        False    4         None        owner=jathan |\n'
            '|                                                         foo=bar      |\n'
            '+----------------------------------------------------------------------+\n'
        )
        assert result.output == expected_output
