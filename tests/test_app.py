# -*- coding: utf-8 -*-

"""
Test the CLI app.
"""

from __future__ import unicode_literals
import logging
import pytest

from .fixtures import (attribute, client, config, device, network, site,
                       site_client)
from .util import CliRunner


log = logging.getLogger(__name__)


__all__ = ('client', 'config', 'site', 'site_client', 'pytest')


#########
# Sites #
#########
def test_site_id(client):
    """Test ``nsot devices list`` without required site_id"""
    runner = CliRunner(client.config)
    with runner.isolated_filesystem():
        result = runner.run('devices list')

        # Make sure it says site-id is required
        expected_output = 'Error: Missing option "-s" / "--site-id".'
        assert result.exit_code == 2
        assert expected_output in result.output


def test_site_add(client):
    """Test ``nsot sites add``."""
    runner = CliRunner(client.config)
    with runner.isolated_filesystem():
        # Make sure it is a positive confirmation.
        result = runner.run("sites add -n Foo -d 'Foo site.'")
        expected_output = "[SUCCESS] Added site!\n"
        assert result.exit_code == 0
        assert result.output == expected_output

        # Try to add the same site again and fail.
        result = runner.run("sites add -n Foo -d 'Foo site.'")
        expected_output = 'Site with this name already exists.\n'
        assert result.exit_code == 1
        assert expected_output in result.output


def test_sites_list(client, site):
    """Test ``nsot sites list``."""
    runner = CliRunner(client.config)
    with runner.isolated_filesystem():
        # Simply list the site successfully.
        result = runner.run('sites list')
        assert result.exit_code == 0
        assert site['name'] in result.output

        # Test -i/--id
        result = runner.run('sites list -i %s' % site['id'])
        assert result.exit_code == 0
        assert site['name'] in result.output

        # Test -n/--name
        result = runner.run('sites list -n %s' % site['name'])
        assert result.exit_code == 0
        assert site['name'] in result.output

        # Test -N/--natural-key
        result = runner.run('sites list -N')
        assert result.exit_code == 0
        assert site['name'] == result.output.strip()


def test_sites_update(client, site):
    """Test ``nsot sites update``."""
    runner = CliRunner(client.config)
    with runner.isolated_filesystem():
        # Change the name.
        result = runner.run('sites update -n Bacon -i %s' % site['id'])
        assert result.exit_code == 0
        assert 'Updated site!' in result.output

        # Update the description
        result = runner.run('sites update -d Sizzle -i %s' % site['id'])
        assert result.exit_code == 0
        assert 'Updated site!' in result.output

        # Assert the bacon sizzles
        result = runner.run('sites list -n Bacon')
        assert result.exit_code == 0
        assert 'Bacon' in result.output
        assert 'Sizzle' in result.output


def test_sites_remove(client, site):
    """Test ``nsot sites remove``."""
    runner = CliRunner(client.config)
    with runner.isolated_filesystem():
        # Just delete the site we have.
        result = runner.run('sites remove -i %s' % site['id'])
        assert result.exit_code == 0
        assert 'Removed site!' in result.output


##############
# Attributes #
##############
def test_attributes_add(site_client):
    """Test ``nsot attributes add``."""
    runner = CliRunner(site_client.config)
    with runner.isolated_filesystem():
        # Create a new attribute
        result = runner.run(
            'attributes add -n device_multi -r device --multi'
        )
        assert result.exit_code == 0


def test_attributes_list(site_client):
    """Test ``nsot attributes list``."""
    runner = CliRunner(site_client.config)
    with runner.isolated_filesystem():
        # Create the monitored attribute
        runner.run('attributes add -n monitored -r device --allow-empty')

        # Simple list
        result = runner.run('attributes list')
        assert result.exit_code == 0

        # Test -N/--natural-key
        result = runner.run('attributes list -N')
        assert result.exit_code == 0
        assert 'Device:monitored\n' == result.output

        # List a single attribute by name
        attr = site_client.attributes.get(name='monitored')[0]
        name_result = runner.run('attributes list -n monitored')

        # Single matching object should have 'Constraints' column
        expected = ('Constraints', 'monitored')
        assert result.exit_code == 0
        for e in expected:
            assert e in name_result.output

        # List the same attribute by id
        id_result = runner.run('attributes list -i %s' % attr['id'])
        assert id_result.exit_code == 0

        # Output should match the previous command.
        assert id_result.output == name_result.output


def test_attributes_update(site_client):
    """Test ``nsot attributes update``."""
    runner = CliRunner(site_client.config)
    with runner.isolated_filesystem():
        # Create and retrieve the multi attribute
        runner.run('attributes add -r device -n multi --multi')
        attr = site_client.attributes.get(name='multi')[0]

        # Display the attribute before update.
        before_result = runner.run('attributes list -i %s' % attr['id'])
        assert before_result.exit_code == 0

        # Update the multi attribute to disable multi
        result = runner.run('attributes update --no-multi -i %s' % attr['id'])
        assert result.exit_code == 0

        # List it to show the proof that the results are not the same.
        after_result = runner.run('attributes list -i %s' % attr['id'])
        assert after_result.exit_code == 0
        assert before_result != after_result


def test_attributes_remove(site_client, attribute):
    """Test ``nsot attributes update``."""
    runner = CliRunner(site_client.config)
    with runner.isolated_filesystem():
        # Just delete the attribute we have.
        result = runner.run('attributes remove -i %s' % attribute['id'])
        assert result.exit_code == 0
        assert 'Removed attribute!' in result.output


###########
# Devices #
###########
def test_device_add(site_client):
    """Test ``nsot devices add``."""
    runner = CliRunner(site_client.config)
    with runner.isolated_filesystem():
        # Success is fun!
        result = runner.run('devices add -H foo-bar1')
        expected_output = '[SUCCESS] Added device!\n'
        assert result.exit_code == 0
        assert result.output == expected_output


def test_devices_bulk_add(site_client):
    """Test ``nsot devices add -b /path/to/bulk_file``"""
    BULK_ADD = (
        'hostname:attributes\n'
        'foo-bar1:owner=jathan\n'
        'foo-bar2:owner=jathan\n'
    )

    # This has an invalid attribute (bacon)
    BULK_FAIL = (
        'hostname:attributes\n'
        'foo-bar3:owner=jathan,bacon=delicious\n'
        'foo-bar4:owner=jathan\n'
    )

    runner = CliRunner(site_client.config)
    with runner.isolated_filesystem():
        # Create the attribute
        runner.run('attributes add -n owner -r device')

        # Write the bulk files.
        with open('bulk_file', 'w') as fh:
            fh.writelines(BULK_ADD)
        with open('bulk_fail', 'w') as fh:
            fh.writelines(BULK_FAIL)

        # Test valid bulk_add
        result = runner.run('devices add -b bulk_file')
        expected_output = (
            "[SUCCESS] Added device!\n"
            "[SUCCESS] Added device!\n"
        )
        assert result.exit_code == 0
        assert result.output == expected_output

        # Test an invalid add
        result = runner.run('devices add -b bulk_fail')
        expected_output = 'Attribute name (bacon) does not exist'
        assert result.exit_code == 1
        assert expected_output in result.output


def test_devices_list(site_client):
    """Test ``nsot devices list``."""
    runner = CliRunner(site_client.config)
    with runner.isolated_filesystem():
        # Create the owner attribute
        runner.run('attributes add -n owner -r device')

        # Create 2 devices w/ owner= set
        runner.run('devices add -H foo-bar1 -a owner=jathan')
        runner.run('devices add -H foo-bar2 -a owner=jathan')

        # Make sure the hostnames show up in a normal list
        result = runner.run('devices list')
        assert result.exit_code == 0

        expected = ('foo-bar1', 'foo-bar2')
        for e in expected:
            assert e in result.output

        # Set query display newline-delimited (default)
        result = runner.run('devices list -q owner=jathan')
        expected_output = (
            'foo-bar1\n'
            'foo-bar2\n'
        )
        assert result.exit_code == 0
        assert result.output == expected_output

        # Test -N/--natural-key
        result = runner.run('devices list -N')
        assert result.exit_code == 0
        assert result.output == expected_output  # Same output as above

        # Set query display comma-delimited (-d/--delimited)
        result = runner.run('devices list -q owner=jathan -d')
        expected_output = 'foo-bar1,foo-bar2\n'
        assert result.exit_code == 0
        assert result.output == expected_output

        # Grep-friendly output (-g/--grep)
        result = runner.run('devices list -a owner=jathan -g')
        expected_output = u'foo-bar1 owner=jathan\nfoo-bar2 owner=jathan\n'
        assert result.exit_code == 0
        assert result.output == expected_output


def test_devices_update(site_client):
    """Test ``nsot devices update``."""
    runner = CliRunner(site_client.config)
    with runner.isolated_filesystem():
        # Create the attributes
        runner.run('attributes add -n owner -r device')
        runner.run('attributes add -n monitored -r device --allow-empty')

        # Create the device w/ owner= set
        runner.run('devices add -H foo-bar1 -a owner=jathan')

        # Now set the 'monitored' attribute
        result = runner.run('devices update -H foo-bar1 -a monitored')
        expected_output = "[SUCCESS] Updated device!\n"
        assert result.exit_code == 0
        assert result.output == expected_output

        # Run a list to assert 'monitored=' attribute is now there.
        result = runner.run('devices list -H foo-bar1')
        assert result.exit_code == 0
        assert 'monitored=' in result.output

        # Now run update by natural_key (hostname) to remove monitored
        result = runner.run('devices update -H foo-bar1 -d -a monitored')
        assert result.exit_code == 0

        # Make sure that monitored isn't showing in output
        result = runner.run('devices list -H foo-bar1')
        assert result.exit_code == 0
        assert 'monitored=' not in result.output


def test_attribute_modify_multi(site_client):
    """Test modification of list-type attributes (multi=True)."""
    runner = CliRunner(site_client.config)
    with runner.isolated_filesystem():
        #####
        # ADD a multi attribute with 2 items
        #####
        # Create the initial device and multi attribute
        runner.run('devices add -H foo-bar1')
        runner.run('attributes add -r device -n multi --multi')

        # Add multi=[jathy, jilli]
        result = runner.run(
            'devices update -H foo-bar1 -a multi=jathy -a multi=jilli -m'
        )
        assert result.exit_code == 0

        # List to see that multi= shows w/ jathy & jilli as values.
        result = runner.run('devices list -H foo-bar1')
        expected = ('multi=', 'jathy', 'jilli')
        assert result.exit_code == 0
        for e in expected:
            assert e in result.output

        #########
        # REPLACE it with two different items
        #########
        # Replace with multi=[bob, alice]
        result = runner.run(
            'devices update -H foo-bar1 -a multi=bob -a multi=alice -m -r'
        )
        assert result.exit_code == 0

        # List to show that multi= shows w/ bob & alice as values.
        result = runner.run('devices list -H foo-bar1')
        expected = ('multi=', 'bob', 'alice')
        assert result.exit_code == 0
        for e in expected:
            assert e in result.output

        ########
        # DELETE one, leaving one
        ########
        # Pop bob
        result = runner.run('devices update -H foo-bar1 -a multi=bob -m -d')
        assert result.exit_code == 0

        # List to show the proof that bob no longer shows!
        result = runner.run('devices list -H foo-bar1')
        assert result.exit_code == 0
        assert 'bob' not in result.output

        ########
        # DELETE the other; attr goes away, object returned to initial state
        ########

        # Pop alice; attribute is removed
        result = runner.run('devices update -H foo-bar1 -a multi=alice -m -d')
        assert result.exit_code == 0

        # List to show the proof that 'multi=' no longer shows in output!
        result = runner.run('devices list -H foo-bar1')
        assert result.exit_code == 0
        assert 'multi=' not in result.output

        #####
        # ADD new list w/ 2 items
        #####
        # Add multi=[spam, eggs]
        result = runner.run(
            'devices update -H foo-bar1 -a multi=spam -a multi=eggs -m'
        )
        assert result.exit_code == 0

        # List to show that 'multi=' is back and has egg & spam.
        result = runner.run('devices list -H foo-bar1')
        expected = ('multi=', 'eggs', 'spam')
        assert result.exit_code == 0
        for e in expected:
            assert e in result.output

        ########
        # DELETE with no value; attribute goes away; object initialized
        ########
        result = runner.run('devices update -H foo-bar1 -a multi -d')
        assert result.exit_code == 0

        # List to show the proof that 'multi=' no longer shows in output. And
        # scene.
        result = runner.run('devices list -H foo-bar1')
        assert result.exit_code == 0
        assert 'multi=' not in result.output


def test_devices_remove(site_client, device):
    """Test ``nsot devices remove``."""
    runner = CliRunner(site_client.config)
    with runner.isolated_filesystem():
        # Just delete the device we have.
        result = runner.run('devices remove -i %s' % device['id'])
        assert result.exit_code == 0
        assert 'Removed device!' in result.output


############
# Networks #
############
def test_network_add(site_client):
    """Test ``nsot networks add``."""
    runner = CliRunner(site_client.config)
    with runner.isolated_filesystem():
        result = runner.run('networks add -c 10.0.0.0/8')
        expected_output = '[SUCCESS] Added network!\n'
        assert result.exit_code == 0
        assert result.output == expected_output


def test_networks_bulk_add(site_client):
    """Test ``nsot networks add -b /path/to/bulk_file``."""
    BULK_ADD = (
        'cidr:attributes\n'
        '10.0.0.0/8:owner=jathan\n'
        '10.0.0.0/24:owner=jathan\n'
    )
    BULK_FAIL = (
        'cidr:attributes\n'
        '10.10.0.0/24:owner=jathan,bacon=delicious\n'
        '10.11.0.0/24:owner=jathan\n'
    )

    runner = CliRunner(site_client.config)
    with runner.isolated_filesystem():
        # Create the owner attribute
        runner.run('attributes add -n owner -r network')

        # Write the bulk files.
        with open('bulk_file', 'w') as fh:
            fh.writelines(BULK_ADD)
        with open('bulk_fail', 'w') as fh:
            fh.writelines(BULK_FAIL)

        # Test *with* provided site_id
        result = runner.run('networks add -b bulk_file')
        expected_output = (
            "[SUCCESS] Added network!\n"
            "[SUCCESS] Added network!\n"
        )
        assert result.exit_code == 0
        assert result.output == expected_output

        # Test an invalid add
        result = runner.run('networks add -b bulk_fail')
        expected_output = 'Attribute name (bacon) does not exist'
        assert result.exit_code == 1
        assert expected_output in result.output


def test_networks_list(site_client):
    """Test ``nsot networks list``."""
    runner = CliRunner(site_client.config)
    with runner.isolated_filesystem():
        # Create the owner attribute
        runner.run('attributes add -n owner -r network')

        # First create our networks w/ owner= set
        runner.run('networks add -c 10.0.0.0/8 -a owner=jathan')
        runner.run('networks add -c 10.0.0.0/24 -a owner=jathan')

        # Make sure 10.0.0.0 shows twice in the output. Lazy man's output
        # checking.
        result = runner.run('networks list')
        assert result.output.count('10.0.0.0') == 2
        assert result.exit_code == 0

        # Set query display newline-delimited (default)
        result = runner.run('networks list -q owner=jathan')
        expected_output = (
            '10.0.0.0/8\n'
            '10.0.0.0/24\n'
        )
        assert result.exit_code == 0
        assert result.output == expected_output

        # Test -N/--natural-key
        result = runner.run('networks list -N')
        assert result.exit_code == 0
        assert result.output == expected_output  # Same output as above

        # Set query display comma-delimited (-d/--delimited)
        result = runner.run('networks list -q owner=jathan -d')
        expected_output = '10.0.0.0/8,10.0.0.0/24\n'
        assert result.exit_code == 0
        assert result.output == expected_output

        # Set query display grep-friendly (--g/--grep)
        result = runner.run('networks list -a owner=jathan -g')
        expected_output = (
            '10.0.0.0/8 owner=jathan\n'
            '10.0.0.0/24 owner=jathan\n'
        )
        assert result.exit_code == 0
        assert result.output == expected_output


def test_networks_subcommands(site_client):
    """Test supernets/subnets sub-commands."""
    runner = CliRunner(site_client.config)
    with runner.isolated_filesystem():
        # Create the owner attribute
        runner.run('attributes add -n owner -r network')

        # Create our networks w/ owner= set
        runner.run('networks add -c 10.0.0.0/8 -a owner=jathan')
        runner.run('networks add -c 10.0.0.0/24 -a owner=jathan')

        # Test subnets: Assert that 10.0.0.0/24 shows in output
        result = runner.run('networks list -c 10.0.0.0/8 subnets')
        expected = ('10.0.0.0', '24')
        assert result.exit_code == 0

        for e in expected:
            assert e in result.output

        # Test supernets: Assert that 10.0.0.0/8 shows in output
        result = runner.run('networks list -c 10.0.0.0/24 supernets')
        expected = ('10.0.0.0', '8')
        assert result.exit_code == 0
        for e in expected:
            assert e in result.output


def test_networks_update(site_client):
    """Test ``nsot networks update``."""
    runner = CliRunner(site_client.config)
    with runner.isolated_filesystem():
        # Create the owner attribute
        runner.run('attributes add -n owner -r network')

        # Create a network & attribute
        runner.run('networks add -c 10.0.0.0/8 -a owner=jathan')
        runner.run('attributes add -n foo -r network')

        # Run the update to add the new attribute
        result = runner.run('networks update -c 10.0.0.0/8 -a foo=bar')
        expected_output = "[SUCCESS] Updated network!\n"
        assert result.exit_code == 0
        assert result.output == expected_output

        # Run a list to see the object w/ the updated result
        result = runner.run('networks list -c 10.0.0.0/8')
        assert result.exit_code == 0
        assert 'foo=bar' in result.output

        # Now run update by natural_key (cidr) to remove foo=bar
        result = runner.run('networks update -c 10.0.0.0/8 -d -a foo')
        assert result.exit_code == 0
        assert 'foo=bar' not in result.output


def test_networks_remove(site_client, network):
    """Test ``nsot networks remove``."""
    runner = CliRunner(site_client.config)
    with runner.isolated_filesystem():
        # Just delete the network we have.
        result = runner.run('networks remove -i %s' % network['id'])
        assert result.exit_code == 0
        assert 'Removed network!' in result.output


##########
# Values #
##########
def test_values_list(site_client):
    """Test ``nsot values list``."""
    runner = CliRunner(site_client.config)
    with runner.isolated_filesystem():
        # Create the owner attribute
        runner.run('attributes add -n owner -r device')

        # Create a single device w/ owner= set
        runner.run('devices add -H foo-bar1 -a owner=jathan')

        # Make sure -n/--name is required.
        result = runner.run('values list')
        assert result.exit_code == 2
        assert 'Error: Missing option "-n"' in result.output

        # Run a simple list to get the expected result.
        result = runner.run('values list -n owner -r device')
        assert result.exit_code == 0
        assert result.output == 'jathan\n'


###########
# Changes #
###########
def test_changes_list(site_client):
    """Test ``nsot changes list``."""
    runner = CliRunner(site_client.config)
    with runner.isolated_filesystem():
        # Just make sure it works.
        result = runner.run('changes list')
        assert result.exit_code == 0
