# -*- coding: utf-8 -*-

"""
Test Protocols in the CLI app.
"""

from __future__ import absolute_import, unicode_literals
import logging

import pytest

from tests.fixtures import (attribute, attributes, client, config, device,
                            interface, network, protocol_type, site,
                            site_client)
from tests.fixtures.circuits import (circuit, circuit_attributes, interface_a,
                                     interface_z, device_a, device_z)
from tests.fixtures.protocols import (protocol, protocols, protocol_attribute,
                                      protocol_attribute2)

from tests.util import CliRunner, assert_output

log = logging.getLogger(__name__)


def test_protocols_add(site_client, device_a, interface_a, site, protocol_type):
    """Test ``nsot protocol add``."""

    device_id = str(device_a['id'])
    interface_id = str(interface_a['id'])

    runner = CliRunner(site_client.config)
    with runner.isolated_filesystem():
        # Add a protocol.
        result = runner.run(
            "protocols add -t bgp -D %s -I %s -e 'my new proto'" % (device_id, interface_id)
        )
        assert result.exit_code == 0
        assert 'Added protocol!' in result.output

        # Verify addition.
        result = runner.run('protocols list')
        assert result.exit_code == 0
        assert 'bgp' in result.output
        assert device_a['hostname'] in result.output
        assert 'my new proto' in result.output

        # Add a second protocol with attributes.
        attributes = 'foo=test_attribute'
        result = runner.run(
            "protocols add -t bgp -D %s -I %s -a %s" % (device_id, interface_id, attributes)
        )
        assert result.exit_code == 0
        assert 'Added protocol!' in result.output

        # Verify addition.
        result = runner.run('protocols list')
        assert result.exit_code == 0
        assert 'bgp' in result.output
        assert device_a['hostname'] in result.output
        assert attributes in result.output


def test_protocols_list(site_client, device_a, interface_a, site, circuit, protocol):
    """Test ``nsot protocols list``"""

    device_id = str(device_a['id'])
    interface_id = str(interface_a['id'])
    protocol_id = str(protocol['id'])

    runner = CliRunner(site_client.config)
    with runner.isolated_filesystem():
        result = runner.run('protocols list')
        assert result.exit_code == 0
        assert 'bgp' in result.output

        # test -t/--type
        result = runner.run('protocols list -t bgp')
        assert result.exit_code == 0
        assert 'bgp' in result.output

        # Test -D/--device
        result = runner.run('protocols list -D %s' % device_id)
        assert result.exit_code == 0
        assert device_a['hostname'] in result.output

        # Test -I/--interface
        result = runner.run('protocols list -I %s' % interface_id)
        assert result.exit_code == 0
        assert interface_a['name_slug'] in result.output

        # Test -a/--attributes
        result = runner.run('protocols list -a foo=test_protocol')
        assert result.exit_code == 0
        assert protocol['attributes']['foo'] in result.output

        # Test -c/--circuit
        result = runner.run('protocols list -c %s' % circuit['name'])
        assert result.exit_code == 0
        assert circuit['name'] in result.output

        # Test -e/--description
        result = runner.run('protocols list -e "%s"' % protocol['description'])
        assert result.exit_code == 0
        assert protocol['description'] in result.output

        # Test -I/--id
        result = runner.run('protocols list -i %s' % protocol_id)
        assert result.exit_code == 0
        assert protocol_id in result.output

        # Test -q/--query
        slug = '{device}:{type}:{id}'.format(**protocol)
        result = runner.run('protocols list -q foo=test_protocol')
        assert result.exit_code == 0
        assert slug in result.output


def test_protocols_list_limit(site_client, protocols):
    """
    If ``--limit 2`` is used, we should only see the first two Protocol objects
    """
    limit = 2
    runner = CliRunner(site_client.config)

    with runner.isolated_filesystem():
        result = runner.run('protocols list -l {}'.format(limit))
        assert result.exit_code == 0

        expected_protocols = protocols[:limit]
        unexpected_protocols = protocols[limit:]

        for p in expected_protocols:
            assert p['device'] in result.output
        for p in unexpected_protocols:
            assert p['device'] not in result.output


def test_protocols_list_offset(site_client, protocols):
    """
    If ``--limit 2`` and ``--offset 2`` are used, we should only see the third
    and fourth Protocol objects that were created
    """
    limit = 2
    offset = 2
    runner = CliRunner(site_client.config)

    with runner.isolated_filesystem():
        result = runner.run('protocols list -l {} -o {}'.format(limit, offset))
        assert result.exit_code == 0

        expected_protocols = protocols[offset:limit+offset]
        unexpected_protocols = protocols[limit+offset:]

        for p in expected_protocols:
            assert p['device'] in result.output
        for p in unexpected_protocols:
            assert p['device'] not in result.output


def test_protocols_update(site_client, interface_a, device_a, site, circuit, protocol, protocol_attribute):
    site_id = str(protocol['site'])
    proto_id = protocol['id']
    runner = CliRunner(site_client.config)
    with runner.isolated_filesystem():
        # Update description
        result = runner.run('protocols update -i %s -e "bees buzz"' % proto_id)
        assert result.exit_code == 0
        assert 'Updated protocol!' in result.output

        # Ensure that buzz is not the bizness
        result = runner.run('protocols list')
        assert result.exit_code == 0
        assert 'buzz' in result.output
        assert 'bizness' not in result.output

        # Add an attribute
        result = runner.run(
            'protocols update -i %s --add-attributes -a boo=test_attribute' % proto_id
        )
        assert result.exit_code == 0
        assert 'Updated protocol!' in result.output

        result = runner.run('protocols list')
        assert result.exit_code == 0
        assert 'test_attribute' in result.output

        # Add an attribute without using --add-attributes.
        result = runner.run(
            'protocols update -i %s -a boo=test_attribute' % proto_id
        )
        assert result.exit_code == 0
        assert 'Updated protocol!' in result.output

        result = runner.run('protocols list')
        assert result.exit_code == 0
        assert 'test_attribute' in result.output

        # Delete an attribute
        result = runner.run(
            'protocols update -i %s --delete-attributes -a foo=test_protocol' % proto_id
        )
        assert result.exit_code == 0
        assert 'Updated protocol!' in result.output

        result = runner.run('protocols list')
        assert result.exit_code == 0
        assert 'test_protocol' not in result.output

        # Replace an attribute
        result = runner.run(
            'protocols update -i %s --replace-attributes -a foo=test_replace' % proto_id
        )
        assert result.exit_code == 0
        assert 'Updated protocol!' in result.output

        result = runner.run('protocols list')
        assert result.exit_code == 0
        assert 'test_protocol' not in result.output
        assert 'test_replace' in result.output


def test_protocols_remove(site_client, protocol):
    runner = CliRunner(site_client.config)

    with runner.isolated_filesystem():
        result = runner.run('protocols remove -i %s -s %s' % (protocol['id'], protocol['site']))
        assert result.exit_code == 0

        result = runner.run('protocols list')
        assert result.exit_code == 0
        assert 'No protocol found' in result.output
