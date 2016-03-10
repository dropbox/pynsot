# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""
Test the CLI app.
"""

import copy
import logging
import os
import pytest
from urllib import urlencode
import re
import shlex

from pynsot import dotfile
from pynsot.app import app

from .fixtures import (
    auth_token_config as config, auth_header_config, AUTH_RESPONSE, API_URL,
    DEVICES_RESPONSE, ATTRIBUTES_RESPONSE, DEVICE_RETRIEVE, DEVICE_UPDATE,
    NETWORK_CREATE, NETWORK_RETRIEVE, NETWORK_UPDATE, NETWORKS_RESPONSE,
    ATTRIBUTE_CREATE, VALUES_RETRIEVE, ATTRIBUTES_NAME_RESPONSE,
    ATTRIBUTES_ID_RESPONSE, DEVICE_HOSTNAME_RETRIEVE, NETWORK_CIDR_RETRIEVE,
    SITES_LIST_RESPONSE, SITES_LIMIT_RESPONSE, CHANGES_LIST_RESPONSE
)
from .util import CliRunner


log = logging.getLogger(__name__)

# Hard-code the app name as 'nsot' to match the CLI util.
app.name = 'nsot'


#########
# Sites #
#########
def test_site_id(config):
    """Test ``nsot devices list`` without required site_id"""
    headers = {'Content-Type': 'application/json'}
    auth_url = config['url'] + '/authenticate/'
    devices_url = config['url'] + '/sites/1/devices/'

    runner = CliRunner(config)
    with runner.isolated_requests() as mock:
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
    with runner.isolated_requests() as mock:
        # Create the site
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.post(sites_url, json=SITE_RESPONSE, headers=headers)

        result = runner.invoke(
            app, shlex.split("sites add -n Foo -d 'Foo site.'")
        )
        assert result.exit_code == 0

        expected_output = (
            "[SUCCESS] Added site!\n"
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
        assert 'This field must be unique.\n' in result.output


def test_sites_list(config):
    """
    Test ``nsot sites list``.
    """
    headers = {'Content-Type': 'application/json'}
    auth_url = config['url'] + '/authenticate/'
    sites_url = config['url'] + '/sites/'

    params = {'limit': 1}
    sites_limit_url = sites_url + '?' + urlencode(params)

    runner = CliRunner(config)
    with runner.isolated_requests() as mock:
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.get(sites_limit_url, json=SITES_LIMIT_RESPONSE, headers=headers)
        mock.get(sites_url, json=SITES_LIST_RESPONSE, headers=headers)
        result = runner.invoke(app, shlex.split('sites list'))

        assert result.exit_code == 0


###########
# Devices #
###########
def test_device_add(config):
    """Test ``nsot devices add -s 1 -H foo-bar1``"""
    headers = {'Content-Type': 'application/json'}
    auth_url = config['url'] + '/authenticate/'
    devices_url = config['url'] + '/sites/1/devices/'

    runner = CliRunner(config)
    with runner.isolated_requests() as mock:
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.post(devices_url, json=DEVICE_RETRIEVE, headers=headers)

        result = runner.invoke(app, shlex.split('devices add -s 1 -H foo-bar1'))
        assert result.exit_code == 0

        expected_output = (
            '[SUCCESS] Added device!\n'
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
    with runner.isolated_requests() as mock:
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
            "[SUCCESS] Added device!\n"
            "[SUCCESS] Added device!\n"
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
    with runner.isolated_requests() as mock:
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.get(devices_url, json=DEVICES_RESPONSE, headers=headers)

        # Normal list
        result = runner.invoke(app, shlex.split('devices list -s 1'))
        assert result.exit_code == 0

        # Make sure the hostnames show up
        expected = ('foo-bar1', 'foo-bar2')
        for e in expected:
            assert e in result.output

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

        # Grep-friendly output (--grep)
        result = runner.invoke(
            app, shlex.split('devices list -s 1 -a owner=jathan -g')
        )
        expected_output = u'foo-bar1 owner=jathan\nfoo-bar2 owner=jathan\n'
        assert result.exit_code == 0
        assert result.output == expected_output


def test_devices_update(config):
    """Test ``nsot devices update -s 1 -i 1 -a monitored``"""
    headers = {'Content-Type': 'application/json'}
    auth_url = config['url'] + '/authenticate/'
    device_uri = config['url'] + '/sites/1/devices/1/'
    devices_url = config['url'] + '/sites/1/devices/'

    update_params = {'hostname': 'foo-bar1', 'limit': 1}
    device_update_url = devices_url + '?' + urlencode(update_params)

    runner = CliRunner(config)
    with runner.isolated_requests() as mock:
        # Run the update to add the new attribute
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.get(device_uri, json=DEVICE_RETRIEVE, headers=headers)
        mock.put(device_uri, json=DEVICE_UPDATE, headers=headers)

        result = runner.invoke(
            app,
            shlex.split('devices update -s 1 -i 1 -a monitored')
        )
        assert result.exit_code == 0

        expected_output = (
            "[SUCCESS] Updated device!\n"
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

        # Assert 'monitored=' attribute is now there.
        assert 'monitored=' in result.output

        # Now run update by natural_key (hostname) to remove monitored
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.get(
            device_update_url, json=DEVICE_HOSTNAME_RETRIEVE, headers=headers
        )
        mock.put(device_uri, json=DEVICE_RETRIEVE, headers=headers)

        result = runner.invoke(
            app,
            shlex.split('devices update -s 1 -H foo-bar1 -d -a monitored')
        )
        assert result.exit_code == 0


def test_attribute_modify(config):
    headers = {'Content-Type': 'application/json'}
    auth_url = config['url'] + '/authenticate/'
    device_uri = config['url'] + '/sites/1/devices/1/'
    devices_url = config['url'] + '/sites/1/devices/'

    runner = CliRunner(config)
    with runner.isolated_requests() as mock:
        # Run the update to ADD the new attribute
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.get(device_uri, json=DEVICE_RETRIEVE, headers=headers)
        mock.put(device_uri, json=DEVICE_UPDATE, headers=headers)

        result = runner.invoke(
            app,
            shlex.split('devices update -s 1 -i 1 -a monitored')
        )
        assert result.exit_code == 0

        # Now REMOVE the attribute
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.get(device_uri, json=DEVICE_RETRIEVE, headers=headers)
        mock.put(device_uri, json=DEVICE_RETRIEVE, headers=headers)
        result = runner.invoke(
            app, shlex.split('devices update -s 1 -i 1 -a monitored -d')
        )
        assert result.exit_code == 0

        # Run a list to see the object w/ the updated result
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.get(device_uri, json=DEVICE_RETRIEVE, headers=headers)

        result = runner.invoke(app, shlex.split('devices list -s 1 -i 1'))
        assert result.exit_code == 0

        # Make sure that monitored isn't showing in output
        assert 'monitored=' not in result.output

        # Test attribute REPLACE


def test_attribute_modify_multi(config):
    """Test modification of list-type attributes (multi=True)."""
    headers = {'Content-Type': 'application/json'}
    auth_url = config['url'] + '/authenticate/'
    device_uri = config['url'] + '/sites/1/devices/1/'
    devices_url = config['url'] + '/sites/1/devices/'

    runner = CliRunner(config)
    with runner.isolated_requests() as mock:

        #####
        # ADD a multi attribute with 2 items
        #####
        INITIAL_DEVICE = {
            'status': 'ok',
            'data': {
                'device': {
                    'attributes': {},
                    'hostname': 'foo-bar1', 'site_id': 1, 'id': 1
                }
            }
        }
        # Add multi=[jathy, jilli]
        MULTI_UPDATE = {
            'status': 'ok',
            'data': {
                'device': {
                    'attributes': {'multi': ['jathy', 'jilli']},
                    'hostname': 'foo-bar1', 'site_id': 1, 'id': 1
                }
            }
        }
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.get(device_uri, json=INITIAL_DEVICE, headers=headers)
        mock.put(device_uri, json=MULTI_UPDATE, headers=headers)

        result = runner.invoke(
            app,
            shlex.split('devices update -s 1 -i 1 -a multi=jathy -a multi=jilli -m')
        )
        assert result.exit_code == 0

        # List to see attributes.
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.get(device_uri, json=MULTI_UPDATE, headers=headers)

        result = runner.invoke(app, shlex.split('devices list -s 1 -i 1'))
        assert result.exit_code == 0

        # Assert that multi= shows w/ jathy & jilli as values.
        expected = ('multi=', 'jathy', 'jilli')
        for e in expected:
            assert e in result.output

        #########
        # REPLACE it with two different items
        #########

        # Replace with multi=[bob, alice]
        MULTI_REPLACE = {
            'status': 'ok',
            'data': {
                'device': {
                    'attributes': {'multi': ['bob', 'alice']},
                    'hostname': 'foo-bar1', 'site_id': 1, 'id': 1
                }
            }
        }
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.get(device_uri, json=MULTI_UPDATE, headers=headers)
        mock.put(device_uri, json=MULTI_REPLACE, headers=headers)

        result = runner.invoke(
            app,
            shlex.split(
                'devices update -s 1 -i 1 -a multi=bob -a multi=alice -m -r'
            )
        )
        assert result.exit_code == 0

        # List to show updated items.
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.get(device_uri, json=MULTI_REPLACE, headers=headers)

        result = runner.invoke(app, shlex.split('devices list -s 1 -i 1'))
        assert result.exit_code == 0

        # Assert that multi= shows w/ bob & alice as values.
        expected = ('multi=', 'bob', 'alice')
        for e in expected:
            assert e in result.output

        ########
        # DELETE one, leaving one
        ########

        # Pop alice
        MULTI_DELETE1 = {
            'status': 'ok',
            'data': {
                'device': {
                    'attributes': {'multi': ['alice']},
                    'hostname': 'foo-bar1', 'site_id': 1, 'id': 1
                }
            }
        }
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.get(device_uri, json=MULTI_REPLACE, headers=headers)
        mock.put(device_uri, json=MULTI_DELETE1, headers=headers)

        result = runner.invoke(
            app, shlex.split('devices update -s 1 -i 1 -a multi=bob -m -d')
        )
        assert result.exit_code == 0

        # List to show the proof!
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.get(device_uri, json=MULTI_DELETE1, headers=headers)

        result = runner.invoke(app, shlex.split('devices list -s 1 -i 1'))
        assert result.exit_code == 0

        # Make sure that bob no longer shows
        assert 'bob' not in result.output

        ########
        # DELETE the other; attr goes away, object returned to initial state
        ########

        # Pop bob; attribute is removed
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.get(device_uri, json=MULTI_DELETE1, headers=headers)
        mock.put(device_uri, json=INITIAL_DEVICE, headers=headers)

        result = runner.invoke(
            app, shlex.split('devices update -s 1 -i 1 -a multi=alice -m -d')
        )
        assert result.exit_code == 0

        # List to show the proof!
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.get(device_uri, json=INITIAL_DEVICE, headers=headers)

        result = runner.invoke(app, shlex.split('devices list -s 1 -i 1'))
        assert result.exit_code == 0

        # Assert that 'multi=' no longer shows in output
        assert 'multi=' not in result.output

        #####
        # ADD new list w/ 2 items
        #####

        # Add multi=[spam, eggs]
        MULTI_ADD2 = {
            'status': 'ok',
            'data': {
                'device': {
                    'attributes': {'multi': ['spam', 'eggs']},
                    'hostname': 'foo-bar1', 'site_id': 1, 'id': 1
                }
            }
        }
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.get(device_uri, json=INITIAL_DEVICE, headers=headers)
        mock.put(device_uri, json=MULTI_ADD2, headers=headers)

        result = runner.invoke(
            app,
            shlex.split(
                'devices update -s 1 -i 1 -a multi=spam -a multi=eggs -m'
            )
        )
        assert result.exit_code == 0

        # List to show updated items.
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.get(device_uri, json=MULTI_ADD2, headers=headers)

        result = runner.invoke(app, shlex.split('devices list -s 1 -i 1'))
        assert result.exit_code == 0

        # Assert that multi= is back and has egg & spam.
        expected = ('multi=', 'eggs', 'spam')
        for e in expected:
            assert e in result.output

        ########
        # DELETE with no value; attribute goes away; object initialized
        ########

        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.get(device_uri, json=MULTI_ADD2, headers=headers)
        mock.put(device_uri, json=INITIAL_DEVICE, headers=headers)

        result = runner.invoke(
            app, shlex.split('devices update -s 1 -i 1 -a multi -d')
        )
        assert result.exit_code == 0

        # List to show the proof!
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.get(device_uri, json=INITIAL_DEVICE, headers=headers)

        result = runner.invoke(app, shlex.split('devices list -s 1 -i 1'))
        assert result.exit_code == 0

        # Assert that 'multi=' no longer shows in output. And scene.
        assert 'multi=' not in result.output



##############
# Attributes #
##############
def test_attributes_list(config):
    """Test ``nsot attributes list -s 1``"""
    headers = {'Content-Type': 'application/json'}
    auth_url = config['url'] + '/authenticate/'
    attrs_url = config['url'] + '/sites/1/attributes/'
    attr_obj_uri = attrs_url + '2/'

    runner = CliRunner(config)
    with runner.isolated_requests() as mock:

        # Simple list
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.get(attrs_url, json=ATTRIBUTES_RESPONSE, headers=headers)

        result = runner.invoke(app, shlex.split('attributes list -s 1'))
        assert result.exit_code == 0

        # List a single attribute by name
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.get(attrs_url, json=ATTRIBUTES_NAME_RESPONSE, headers=headers)

        name_result = runner.invoke(
            app, shlex.split('attributes list -s 1 -n monitored')
        )

        # Single matching object should have 'Constraints' column
        expected = ('Constraints', 'monitored')
        for e in expected:
            assert e in name_result.output

        # List the same attribute by id
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.get(attr_obj_uri, json=ATTRIBUTES_ID_RESPONSE, headers=headers)

        id_result = runner.invoke(
            app, shlex.split('attributes list -s 1 -i 2')
        )
        # Output should match the previous command.
        assert id_result.output == name_result.output


def test_attributes_add(config):
    headers = {'Content-Type': 'application/json'}
    auth_url = config['url'] + '/authenticate/'
    attrs_url = config['url'] + '/sites/1/attributes/'

    runner = CliRunner(config)
    with runner.isolated_requests() as mock:
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.post(attrs_url, json=ATTRIBUTE_CREATE, headers=headers)

        result = runner.invoke(
            app, shlex.split('attributes add -s 1 -n multi -r device --multi')
        )
        assert result.exit_code == 0


def test_attributes_update(config):
    headers = {'Content-Type': 'application/json'}
    auth_url = config['url'] + '/authenticate/'
    attrs_url = config['url'] + '/sites/1/attributes/'
    attr_uri = config['url'] + '/sites/1/attributes/3/'

    runner = CliRunner(config)

    ATTRIBUTE_UPDATE = ATTRIBUTE_CREATE.copy()['data']['attribute']
    ATTRIBUTE_UPDATE['multi'] = False

    with runner.isolated_requests() as mock:
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.get(attr_uri, json=ATTRIBUTE_CREATE, headers=headers)
        mock.put(attr_uri, json=ATTRIBUTE_UPDATE, headers=headers)

        # Update the attribute to disable multi
        result = runner.invoke(
            app, shlex.split('attributes update -s 1 -i 3 --no-multi')
        )
        assert result.exit_code == 0

        # List it to show the proof!
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.get(attr_uri, json=ATTRIBUTE_CREATE, headers=headers)
        result = runner.invoke(
            app, shlex.split('attributes list -s 1 -i 3')
        )
        assert result.exit_code == 0

        # Make sure that 'multi' name is in the output.
        assert 'multi' in result.output

############
# Networks #
############
def test_network_add(config):
    """Test ``nsot networks add -s 1 -c 10.0.0.0/8``"""
    headers = {'Content-Type': 'application/json'}
    auth_url = config['url'] + '/authenticate/'
    networks_url = config['url'] + '/sites/1/networks/'

    runner = CliRunner(config)
    with runner.isolated_requests() as mock:
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.post(networks_url, json=NETWORK_CREATE, headers=headers)

        result = runner.invoke(app, shlex.split('networks add -s 1 -c 10.0.0.0/8'))
        assert result.exit_code == 0

        expected_output = (
            '[SUCCESS] Added network!\n'
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
    with runner.isolated_requests() as mock:
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
            "[SUCCESS] Added network!\n"
            "[SUCCESS] Added network!\n"
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
    with runner.isolated_requests() as mock:
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.get(networks_url, json=NETWORKS_RESPONSE, headers=headers)

        result = runner.invoke(app, shlex.split('networks list -s 1'))
        assert result.exit_code == 0

        # Make sure 10.0.0.0 shows twice in the output. Lazy man's output
        # checking.
        assert result.output.count('10.0.0.0') == 2

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

        # Set query display comma-delimited (--delimited)
        result = runner.invoke(
            app, shlex.split('networks list -s 1 -a owner=jathan -g')
        )
        assert result.exit_code == 0

        expected_output = (
            '10.0.0.0/8 owner=jathan\n'
            '10.0.0.0/24 owner=jathan\n'
        )
        assert result.output == expected_output


def test_networks_subcommands(config):
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
            'state': 'allocated',
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
                'state': 'allocated',
                'site_id': 1}
            ],
            'offset': 0,
            'total': 1},
        'status': 'ok'
    }

    runner = CliRunner(config)
    with runner.isolated_requests() as mock:
        # Test subnets
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.get(network_match, json=SUBNETS, headers=headers)

        result = runner.invoke(
            app, shlex.split('networks list -s 1 -c 10.0.0.0/8 subnets')
        )
        assert result.exit_code == 0

        # Assert that 10.0.0.0/24 shows in output
        expected = ('10.0.0.0', '24')
        for e in expected:
            assert e in result.output

        # Test supernets
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.get(network_match, json=SUPERNETS, headers=headers)

        result = runner.invoke(
            app, shlex.split('networks list -s 1 -c 10.0.0.0/24 supernets')
        )
        assert result.exit_code == 0

        # Assert that 10.0.0.0/8 shows in output
        expected = ('10.0.0.0', '8')
        for e in expected:
            assert e in result.output


def test_networks_update(config):
    """Test ``nsot networks update -s 1 -i 1 -a foo=bar``"""
    headers = {'Content-Type': 'application/json'}
    auth_url = config['url'] + '/authenticate/'
    networks_url = config['url'] + '/sites/1/networks/'
    network_uri = config['url'] + '/sites/1/networks/1/'

    update_params = {'cidr': '10.0.0.0/8', 'limit': 1}
    network_update_url = networks_url + '?' + urlencode(update_params)

    runner = CliRunner(config)
    with runner.isolated_requests() as mock:
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
            "[SUCCESS] Updated network!\n"
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

        # Assert that foo=bar is in the output
        assert 'foo=bar' in result.output

        # Now run update by natural_key (cidr) to remove foo=bar
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.get(
            network_update_url, json=NETWORK_CIDR_RETRIEVE, headers=headers
        )
        mock.put(network_uri, json=NETWORK_RETRIEVE, headers=headers)

        result = runner.invoke(
            app,
            shlex.split('networks update -s 1 -c 10.0.0.0/8 -d -a foo')
        )
        assert result.exit_code == 0


def test_values_list(config):
    """Test ``nsot devices list -s 1 -n owner -r device``."""
    headers = {'Content-Type': 'application/json'}
    auth_url = config['url'] + '/authenticate/'
    values_uri = config['url'] + '/sites/1/values/'
    values_url = values_uri + '?resource_name=Device&site_id=1&name=owner'

    runner = CliRunner(config)
    with runner.isolated_requests() as mock:
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.get(
            values_url,
            json=VALUES_RETRIEVE, headers=headers
        )

        # Make sure -n/--name is required.
        result = runner.invoke(app, shlex.split('values list'))
        assert result.exit_code != 0
        assert 'Error: Missing option "-n"' in result.output

        # Run a simple list to get the expected result.
        result = runner.invoke(
            app,
            shlex.split('values list -s 1 -n owner -r device')
        )
        assert result.exit_code == 0
        assert result.output == 'jathan\n'


###########
# Changes #
###########
def test_changes_list(config):
    """
    Test ``nsot changes list``.
    """
    headers = {'Content-Type': 'application/json'}
    auth_url = config['url'] + '/authenticate/'
    changes_url = config['url'] + '/sites/1/changes/'

    params = {'limit': 1}
    changes_limit_url = changes_url + '?' + urlencode(params)

    CHANGES_LIMIT_RESPONSE = CHANGES_LIST_RESPONSE.copy()
    CHANGES_LIMIT_RESPONSE['limit'] = 1

    runner = CliRunner(config)
    with runner.isolated_requests() as mock:
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.get(changes_limit_url, json=CHANGES_LIMIT_RESPONSE, headers=headers)
        mock.get(changes_url, json=CHANGES_LIST_RESPONSE, headers=headers)
        result = runner.invoke(app, shlex.split('changes list'))

        assert result.exit_code == 0
