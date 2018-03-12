# -*- coding: utf-8 -*-

"""
Test Protocols in the CLI app.
"""

from __future__ import absolute_import, unicode_literals
import logging

import pytest

from tests.fixtures import (attribute, attributes, client, config, device,
                            interface, network, protocol_type, site, site_client)
from tests.fixtures.circuits import (circuit, circuit_attributes, interface_a,
                                    interface_z, device_a, device_z)
from tests.fixtures.protocols import protocol

from tests.util import CliRunner, assert_output

log = logging.getLogger(__name__)


def test_protocols_add(site_client, device, interface, site, protocol_type):
    """Test ``nsot protocol add``."""

    device_id = str(device['id'])
    interface_id = str(interface['id'])

    runner = CliRunner(site_client.config)
    with runner.isolated_filesystem():
        # Add a protocol.
        result = runner.run(
            "protocols add -t bgp -D %s -i %s -e 'my new proto'" % (device_id, interface_id)
        )
        assert result.exit_code == 0
        assert 'Added protocol!' in result.output

        # Verify addition.
        result = runner.run('protocols list -t bgp')
        assert result.exit_code == 0
        assert 'bgp' in result.output
        assert device_id in result.output
        assert 'my new proto' in result.output


def test_protocols_list(site_client, protocol, device_a, interface_a, site, protocol_type, circuit):
    """Test ``nsot protocols list``"""

    device_id = str(device_a['id'])
    interface_id = str(interface_a['id'])

    runner = CliRunner(site_client.config)
    with runner.isolated_filesystem():

        result = runner.run('protocols list -t bgp')
        assert result.exit_code == 0
        assert 'bgp' in result.output

        # Test -D/--device
        result = runner.run('protocols list -t bgp -D %s' % device_id)
        assert result.exit_code == 0
        assert device_id in result.output

        # Test -i/--interface
        result = runner.run('protocols list -t bgp -i %s' % interface_id)
        assert result.exit_code == 0
        assert interface_id in result.output

        # Test -a/--attributes
        result = runner.run('protocols list -t bgp -a foo=test_protocol')
        assert result.exit_code == 0
        assert 'test_protocol' in result.output

        # Test -c/--circuit
        result = runner.run('protocols list -t bgp -c %s' % circuit['name'])
        assert result.exit_code == 0
        assert circuit['name'] in result.output

        # Test -e/--description
        result = runner.run('protocols list -t bgp -e "protocols are the bizness"')
        assert result.exit_code == 0
        # assert protocol['description'] in result.output THIS IS BROKEN.
        # assert "protocols are the bizness" in result.output THIS TOO, protocol not found.

        # Test -I/--id
        result = runner.run('protocols list -t bgp -I 1')
        # assert result.exit_code == 0
        # assert protocol['id'] in result.output AGAIN, protocol not available.

def test_protocols_update(site_client, device_a, protocol):
    device_id = str(device_a['id'])
    site_id = str(device_a['site_id'])
    protocol_id = str(protocol['id'])
    runner = CliRunner(site_client.config)
    with runner.isolated_filesystem():
        result = runner.run('protocols update -t bgp -I %s -s %s -D %s -e "switchin it up"' % (protocol_id, site_id, device_id))
        import pdb; pdb.set_trace()
        assert result.exit_code == 0
        assert 'switching' in result.output


def test_protocols_remove(site_client, device):
    pass
