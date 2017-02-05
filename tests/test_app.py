# -*- coding: utf-8 -*-

"""
Test the CLI app.
"""

from __future__ import unicode_literals
import logging

import pytest

from .fixtures import (attribute, client, config, device, network, interface,
                       site, site_client)
from .util import CliRunner, assert_output


log = logging.getLogger(__name__)


__all__ = ('client', 'config', 'site', 'site_client', 'pytest', 'attribute',
           'device', 'interface', 'network')


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
        expected_output = 'site with this name already exists.\n'
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
        assert_output(result, ['Added attribute!'])


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
        # Create and retrieve the 'tags' attribute as a list type
        runner.run('attributes add -r device -n tags --multi')
        attr = site_client.attributes.get(name='tags')[0]

        # Display the attribute before update.
        before_result = runner.run('attributes list -i %s' % attr['id'])
        assert_output(before_result, ['tags', 'Device'])

        # Update the tags attribute to disable multi
        result = runner.run('attributes update --no-multi -i %s' % attr['id'])
        assert_output(result, ['Updated attribute!'])

        # List it to show the proof that the results are not the same.
        after_result = runner.run('attributes list -i %s' % attr['id'])
        assert after_result.exit_code == 0
        assert before_result != after_result

        # Update attribute by natural_key (name, resource_name)
        runner.run(
            'attributes update -r device -n tags --allow-empty'
        )
        result = runner.run('attributes list -r device -n tags')
        assert_output(result, ['allow_empty=True'])

        # Run update without optional args
        result = runner.run('attributes update -r device -n tags')
        assert_output(result, ['Error:'], exit_code=2)


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

        # Set query with --l/--limit
        result = runner.run('devices list -l 1 -q owner=jathan')
        expected_output = 'foo-bar1\n'
        assert result.exit_code == 0
        assert result.output == expected_output

        # Set query with --l/--limit and -o/--offset
        result = runner.run('devices list -l 1 -o 1 -q owner=jathan')
        expected_output = 'foo-bar2\n'
        assert result.exit_code == 0
        assert result.output == expected_output

        # Grep-friendly output (-g/--grep)
        result = runner.run('devices list -a owner=jathan -g')
        expected_output = u'foo-bar1 owner=jathan\nfoo-bar2 owner=jathan\n'
        assert result.exit_code == 0
        assert result.output == expected_output

        # Now create 1 device w/ owner= w/ a space in the value
        runner.run('devices add -H foo-bar3 -a owner="Jathan McCollum"')

        # Test that you can query by values w/ spaces when properly quoted
        result = runner.run('devices list -q \'owner="Jathan McCollum"\'')
        expected_output = 'foo-bar3\n'
        assert result.exit_code == 0
        assert result.output == expected_output

        # ... Or using backslashes works, too.
        result = runner.run('devices list -q "owner=Jathan\ McCollum"')
        assert result.exit_code == 0
        assert result.output == expected_output

        # Test that query with unbalanced quotes fails.
        result = runner.run('devices list -q \'owner="Jathan McCollum\'')
        assert result.exit_code == 1
        assert 'No closing quotation' in result.output


def test_devices_subcommands(site_client, device):
    """Test ``nsot devices list ... interfaces`` sub-command."""
    runner = CliRunner(site_client.config)
    with runner.isolated_filesystem():
        # Create two interfaces on the device.
        hostname = device['hostname']
        device_id = device['id']
        runner.run('interfaces add -D %s -n eth0' % device_id)
        runner.run('interfaces add -D %s -n eth1' % device_id)

        # Lookup using natural_key (hostname)
        result = runner.run('devices list -H %s interfaces' % hostname)
        expected = ('eth0', 'eth1')
        assert result.exit_code == 0
        for e in expected:
            assert e in result.output

        # Lookup by id
        result = runner.run('devices list -i %s interfaces' % device_id)
        assert result.exit_code == 0
        for e in expected:
            assert e in result.output


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
        result = runner.run(
            'devices update -H foo-bar1 -a monitored --delete-attributes'
        )
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
            'devices update -H foo-bar1 -a multi=jathy -a multi=jilli --multi'
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
            'devices update -H foo-bar1 -a multi=bob -a multi=alice --multi '
            '--replace-attributes'
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
        result = runner.run(
            'devices update -H foo-bar1 -a multi=bob --multi '
            '--delete-attributes'
        )
        assert result.exit_code == 0

        # List to show the proof that bob no longer shows!
        result = runner.run('devices list -H foo-bar1')
        assert result.exit_code == 0
        assert 'bob' not in result.output

        ########
        # DELETE the other; attr goes away, object returned to initial state
        ########

        # Pop alice; attribute is removed
        result = runner.run(
            'devices update -H foo-bar1 -a multi=alice --multi '
            '--delete-attributes'
        )
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
            'devices update -H foo-bar1 -a multi=spam -a multi=eggs --multi'
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
        result = runner.run(
            'devices update -H foo-bar1 -a multi --delete-attributes'
        )
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
        assert_output(result, ['Removed device!'])

        # Create another device and delete it by hostname using -H
        runner.run('devices add -H delete-me')
        result = runner.run('devices remove -i delete-me')
        assert_output(result, ['Removed device!'])

        # Create another device and delete it by hostname using -H
        runner.run('devices add -H delete-me')
        result = runner.run('devices remove -H delete-me')
        assert_output(result, ['Removed device!'])


############
# Networks #
############
def test_networks_add(site_client):
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

        # Set query w/ -l/--limit
        result = runner.run('networks list -l 1 -q owner=jathan')
        expected_output = '10.0.0.0/8\n'
        assert result.exit_code == 0
        assert result.output == expected_output

        # Set query w/ -l/--limit & -o/--offset
        result = runner.run('networks list -l 1 -o 1 -q owner=jathan')
        expected_output = '10.0.0.0/24\n'
        assert result.exit_code == 0
        assert result.output == expected_output

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

        # Now create 1 network w/ owner= w/ a space in the value
        runner.run('networks add -c 10.0.0.0/16 -a owner="Jathan McCollum"')

        # Test that you can query by values w/ spaces when properly quoted
        result = runner.run('networks list -q \'owner="Jathan McCollum"\'')
        expected_output = '10.0.0.0/16\n'
        assert result.exit_code == 0
        assert result.output == expected_output

        # ... Or using backslashes works, too.
        result = runner.run('networks list -q "owner=Jathan\ McCollum"')
        assert result.exit_code == 0
        assert result.output == expected_output

        # Test that query with unbalanced quotes fails.
        result = runner.run('networks list -q \'owner="Jathan McCollum\'')
        assert result.exit_code == 1
        assert 'No closing quotation' in result.output


def test_networks_subcommands(site_client):
    """Test ``nsot networks list ... <subcommand>``."""
    runner = CliRunner(site_client.config)
    with runner.isolated_filesystem():
        # Create the owner attribute
        runner.run('attributes add -n owner -r network')

        # Create our networks w/ owner= set
        runner.run('networks add -c 10.0.0.0/8 -a owner=jathan')
        runner.run('networks add -c 10.0.0.0/24 -a owner=jathan')

        # Test subnets: Assert that 10.0.0.0/24 shows in output
        result = runner.run('networks list -c 10.0.0.0/8 subnets')
        assert_output(result, ['10.0.0.0', '24'])

        # Test supernets: Assert that 10.0.0.0/8 shows in output
        result = runner.run('networks list -c 10.0.0.0/24 supernets')
        assert_output(result, ['10.0.0.0', '8'])

        # Let's add some more networks for fun.
        runner.run('networks add -c 10.10.10.0/24')
        runner.run('networks add -c 10.10.10.1/32')
        runner.run('networks add -c 10.10.10.2/32')
        runner.run('networks add -c 10.10.10.3/32')

        # Test parent
        result = runner.run('networks list -c 10.10.10.1/32 parent')
        assert_output(result, ['10.10.10.0', '24'])

        # Test ancestors
        result = runner.run('networks list -c 10.10.10.1/32 ancestors')
        assert_output(result, ['10.10.10.0', '24'])
        assert_output(result, ['10.0.0.0', '8'])

        # Test children
        result = runner.run('networks list -c 10.10.10.0/24 children')
        assert_output(result, ['10.10.10.1', '32'])
        assert_output(result, ['10.10.10.2', '32'])
        assert_output(result, ['10.10.10.3', '32'])

        # Test descendants
        result = runner.run('networks list -c 10.0.0.0/8 descendants')
        assert_output(result, ['10.0.0.0', '24'])
        assert_output(result, ['10.10.10.0', '24'])
        assert_output(result, ['10.10.10.1', '32'])
        assert_output(result, ['10.10.10.2', '32'])
        assert_output(result, ['10.10.10.3', '32'])

        # Assert descendents (typoed) includes deprecation warning
        result2 = runner.run('networks list -c 10.0.0.0/8 descendents')
        assert_output(result2, ['[WARNING]'])
        assert result.output.splitlines() == result2.output.splitlines()[1:]

        # Test root
        result = runner.run('networks list -c 10.10.10.1/32 root')
        assert_output(result, ['10.0.0.0', '8'])

        # Test siblings
        result = runner.run('networks list -c 10.10.10.2/32 siblings')
        assert_output(result, ['10.10.10.1', '32'])
        assert_output(result, ['10.10.10.3', '32'])

        # Test siblings w/ --include-self
        result = runner.run(
            'networks list -c 10.10.10.2/32 siblings --include-self'
        )
        assert_output(result, ['10.10.10.1', '32'])
        assert_output(result, ['10.10.10.2', '32'])
        assert_output(result, ['10.10.10.3', '32'])

        # Test closest_parent PASS w/ non-existent network
        result = runner.run('networks list -c 10.10.10.104/32 closest_parent')
        assert_output(result, ['10.10.10.0', '24'])

        # Test closest_parent FAIL w/ non-existent parent
        result = runner.run('networks list -c 1.2.3.4/32 closest_parent')
        assert_output(result, ['No such Network found'], exit_code=1)


def test_networks_allocation(site_client, device, network, interface):
    """Test network allocation-related subcommands."""
    runner = CliRunner(site_client.config)
    with runner.isolated_filesystem():
        # network = 10.20.30.0/24
        # leaf = 10.20.30.1/32

        # Test assignments
        result = runner.run('networks list -c 10.20.30.1/32 assignments')
        assert_output(result, ['foo-bar1', 'eth0'])

        # Test reserved
        runner.run('networks add -c 10.20.30.104/32 --state reserved')
        result = runner.run('networks list reserved')
        assert_output(result, ['10.20.30.104', '32'])

        # Test next_network
        result = runner.run(
            'networks list -c 10.20.30.0/24 next_network -n 2 -p 28'
        )
        assert_output(result, ['10.20.30.16', '28'])
        assert_output(result, ['10.20.30.32', '28'])

        # Test next_address
        runner.run('networks add -c 10.20.30.3/32')
        result = runner.run('networks list -c 10.20.30.0/24 next_address -n 3')
        assert_output(result, ['10.20.30.2', '32'])
        assert_output(result, ['10.20.30.4', '32'])
        assert_output(result, ['10.20.30.5', '32'])

        #Test strict allocations
        runner.run('networks add -c 10.2.1.0/24')
        runner.run('networks add -c 10.2.1.0/25')
        result = runner.run('networks list -c 10.2.1.0/24 next_network -p 28 -n 3 -s')
        assert_output(result, ['10.2.1.128', '28'])
        assert_output(result, ['10.2.1.144', '28'])
        assert_output(result, ['10.2.1.160', '28'])

        #Test strict allocations for next_address
        result = runner.run('networks list -c 10.2.1.0/24 next_address -n 3 -s')
        assert_output(result, ['10.2.1.128', '32'])
        assert_output(result, ['10.2.1.129', '32'])
        assert_output(result, ['10.2.1.130', '32'])

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
        result = runner.run(
            'networks update -c 10.0.0.0/8 -a foo --delete-attributes'
        )
        assert result.exit_code == 0
        assert 'foo=bar' not in result.output


def test_networks_remove(site_client, network):
    """Test ``nsot networks remove``."""
    runner = CliRunner(site_client.config)
    with runner.isolated_filesystem():
        # Just delete the network we have by id.
        result = runner.run('networks remove -i %s' % network['id'])
        assert result.exit_code == 0
        assert 'Removed network!' in result.output

        # Create a new network and then delete it by CIDR using -i.
        runner.run('networks add -c 10.20.30.0/24')
        result = runner.run('networks remove -i 10.20.30.0/24')
        assert_output(result, ['Removed network!'])

        # Create a another network and then delete it by CIDR using -c.
        runner.run('networks add -c 10.20.30.0/24')
        result = runner.run('networks remove -c 10.20.30.0/24')
        assert_output(result, ['Removed network!'])


##############
# Interfaces #
##############
def test_interfaces_add(site_client, device):
    """Test ``nsot interfaces add``."""
    device_id = device['id']

    runner = CliRunner(site_client.config)
    with runner.isolated_filesystem():
        # Add an interface by id (natural_key not yet supported)
        result = runner.run(
            "interfaces add -D %s -n eth0 -e 'this is eth0'" % device_id
        )
        assert result.exit_code == 0
        assert 'Added interface!' in result.output

        # Verify addition.
        result = runner.run('interfaces list -D %s' % device_id)
        assert result.exit_code == 0
        assert 'eth0' in result.output

        # Create another interface and assign an address to it.
        runner.run('networks add -c 10.10.10.0/24')
        add_result = runner.run(
            'interfaces add -D %s -n eth1 -c 10.10.10.1/32' % device_id
        )
        assert add_result.exit_code == 0

        # Verify addition/assignment.
        result = runner.run('interfaces list -D %s' % device_id)
        assert result.exit_code == 0
        expected = ('eth0', '10.10.10.1/32')
        for e in expected:
            assert e in result.output

        # Create a new interface w/ multiple addresses assigned
        add_result = runner.run(
            'interfaces add -D %s -n eth2 -c 10.10.10.2/32 -c 10.10.10.3/32' %
            device_id
        )
        assert add_result.exit_code == 0

        # Verify it was happy.
        result = runner.run('interfaces list -D %s -n eth2' % device_id)
        assert result.exit_code == 0
        expected = ('10.10.10.2/32', '10.10.10.3/32')
        for e in expected:
            assert e in result.output

        # Test setting parent_id (-p/--parent-id) on create
        parent_ifc = site_client.interfaces.get(name='eth0')[0]
        parent_id = parent_ifc['id']
        result = runner.run(
            'interfaces add -D %s -n eth0:1 -p %s' % (device_id, parent_id)
        )
        assert result.exit_code == 0
        assert 'Added interface!' in result.output


def test_interfaces_list(site_client, device):
    """Test ``nsot interfaces list``."""
    device_id = device['id']
    hostname = device['hostname']

    runner = CliRunner(site_client.config)
    with runner.isolated_filesystem():
        # Add an interface attribute: vlan
        runner.run('attributes add -r interface -n vlan')

        # And a network we can assign addresses from
        runner.run('networks add -c 10.10.10.0/24')

        # Add a couple interfaces to the device
        # eth0: vlan=100, mac=1, speed=10000, type=6 (default)
        i1 = runner.run(
            'interfaces add -D %s -n eth0 -a vlan=100 -m 00:00:00:00:00:01 '
            '-S 10000 -c 10.10.10.1/32' % device_id
        )
        assert i1.exit_code == 0
        # eth1: vlan=100, mac=2, speed=20000, type=24
        i2 = runner.run(
            'interfaces add -D %s -n eth1 -a vlan=100 -m 00:00:00:00:00:02 '
            '-S 20000 -c 10.10.10.2/32 -t 24' % device_id
        )
        assert i2.exit_code == 0

        # Basic list: Make sure both interfaces appear.
        result = runner.run('interfaces list')
        assert result.exit_code == 0
        expected = ('eth0', 'eth1')
        for e in expected:
            assert e in result.output

        ############
        # Querying #
        ############

        # Set query -q/--query
        result = runner.run('interfaces list -q vlan=100')
        expected_output = '{0}:eth0\n{0}:eth1\n'.format(hostname)
        assert result.exit_code == 0
        assert result.output == expected_output

        # Natural key output -N/--natural-key should have same output as -q
        result = runner.run('interfaces list -a vlan=100 -N')
        assert result.exit_code == 0
        assert result.output == expected_output

        # Set query display comma-delimited (-d/--delimited)
        result = runner.run('interfaces list -q vlan=100 -d')
        expected_output = '{0}:eth0,{0}:eth1\n'.format(hostname)
        assert result.exit_code == 0
        assert result.output == expected_output

        # Set query w/ -l/--limit
        result = runner.run('interfaces list -l1 -q vlan=100')
        expected_output = '{0}:eth0\n'.format(hostname)
        assert result.exit_code == 0
        assert result.output == expected_output

        # Set query w/ -l/--limit and -o/--offset
        result = runner.run('interfaces list -l1 -o1 -q vlan=100')
        expected_output = '{0}:eth1\n'.format(hostname)
        assert result.exit_code == 0
        assert result.output == expected_output

        # Grep-friendly output (-g/--grep)
        result = runner.run('interfaces list -a vlan=100 -g')
        expected_output = (
            '{0}:eth0 vlan=100\n'
            '{0}:eth1 vlan=100\n'
        ).format(hostname)
        assert result.exit_code == 0
        assert result.output == expected_output

        # Query by natural key
        result = runner.run('interfaces list -i {0}:eth1'.format(hostname))
        assert 'eth1' in result.output
        assert str(device_id) in result.output
        assert result.exit_code == 0

        ###########
        # Filtering
        ###########

        # Filter by -D/--device (by id)
        result = runner.run('interfaces list -D %s' % device_id)
        expected = ('eth0', 'eth1')
        assert result.exit_code == 0
        for e in expected:
            assert e in result.output

        # Filter by -D/--device (by hostname) should have same output as by id
        result = runner.run('interfaces list -D %s' % hostname)
        assert result.exit_code == 0
        for e in expected:
            assert e in result.output

        # Filter by -n/--name
        result = runner.run('interfaces list -D %s -n eth1' % hostname)
        assert result.exit_code == 0
        assert 'eth1' in result.output
        assert 'eth0' not in result.output

        # Filter by -S/--speed
        result = runner.run('interfaces list -D %s -S 10000' % hostname)
        assert result.exit_code == 0
        assert 'eth0' in result.output
        assert 'eth1' not in result.output

        # Filter by -t/--type
        result = runner.run('interfaces list -D %s -t 24' % hostname)
        assert result.exit_code == 0
        assert 'eth1' in result.output
        assert 'eth0' not in result.output

        # Filter by -m/--mac-address
        result = runner.run('interfaces list -D %s -m 2' % hostname)
        assert result.exit_code == 0
        assert 'eth1' in result.output
        assert 'eth0' not in result.output


def test_interfaces_subcommands(site_client, device):
    """Test ``nsot interfaces list ... {subcommand}``."""
    device_id = device['id']
    device_hostname = device['hostname']

    runner = CliRunner(site_client.config)
    with runner.isolated_filesystem():
        # Add an interface attribute: vlan
        runner.run('attributes add -r interface -n vlan')

        # And a network for address assignments
        runner.run('networks add -c 10.10.10.0/24')

        # Add a couple interfaces to the device
        # eth0: vlan=100, mac=1, speed=10000, type=6 (default)
        i1 = runner.run(
            'interfaces add -D %s -n eth0 -a vlan=100 -m 00:00:00:00:00:01 '
            '-S 10000 -c 10.10.10.1/32 -c 10.10.10.2/32' % device_id
        )
        assert i1.exit_code == 0

        # Test addresses
        cmds = [
            'interfaces list -D %s -n eth0 -N addresses' % device_id,
            'interfaces list -i %s:eth0 -N addresses' % device_hostname
        ]

        for cmd in cmds:
            result = runner.run(cmd)
            assert result.exit_code == 0
            assert result.output == '10.10.10.1/32\n10.10.10.2/32\n'

        # Test networks
        cmds = [
            'interfaces list -D %s -n eth0 -N networks' % device_id,
            'interfaces list -i %s:eth0 -N networks' % device_hostname
        ]

        for cmd in cmds:
            result = runner.run(cmd)
            assert result.exit_code == 0
            assert result.output == '10.10.10.0/24\n'

        # Test assignments
        cmds = [
            'interfaces list -D %s -n eth0 -N assignments' % device_id,
            'interfaces list -i %s:eth0 -N assignments' % device_hostname
        ]
        for cmd in cmds:
            result = runner.run(cmd)
            expected_output = (
                'foo-bar1:eth0:10.10.10.1/32\n'
                'foo-bar1:eth0:10.10.10.2/32\n'
            )
            assert result.exit_code == 0
            assert result.output == expected_output


def test_interfaces_update(site_client, device):
    """Test ``nsot interfaces update``."""
    device_id = device['id']
    hostname = device['hostname']

    runner = CliRunner(site_client.config)
    with runner.isolated_filesystem():
        # Create some attributes
        runner.run('attributes add -n vlan -r interface')
        runner.run('attributes add -n metro -r interface')

        # Create a network for address assignments
        runner.run('networks add -c 10.10.10.0/24')

        # Create an interface w/ attributes set
        # eth0:
        #    vlan=100, metro=lax, mac_address=00:00:00:00:00:01, speed=40000,
        #    type=24, description='this is my eth0', ip=10.10.10.1/32
        runner.run(
            "interfaces add -D %s -n eth0 -a vlan=100 -a metro=lax -m 1 -S "
            "40000 -e 'this is my eth0' -t 24 -c 10.10.10.1/32" % device_id
        )
        parent_ifc = site_client.interfaces.get(name='eth0')[0]
        parent_id = parent_ifc['id']

        # Create a child interface to eth0
        # eth0:1:
        #    ip = 10.10.10.2/32, mac_address=00:00:00:00:00:02
        runner.run(
            "interfaces add -D %s -n eth0:1 -c 10.10.10.2/32" % device_id
        )
        child_ifc = site_client.interfaces.get(name='eth0:1')[0]
        child_id = child_ifc['id']

        # Test attributes: update vlan=N
        cases = [
            [200, parent_id],
            [300, '%s:%s' % (hostname, parent_ifc['name'])],
        ]

        for vlan, identifier in cases:
            result = runner.run(
                'interfaces update -i %s -a vlan=%d' % (identifier, vlan)
            )
            assert result.exit_code == 0
            assert 'Updated interface!' in result.output

            # Verify attribute update
            result = runner.run('interfaces list -i %s' % identifier)
            assert result.exit_code == 0
            assert 'vlan=%d' % (vlan) in result.output

        # Test parent: update eth0:1 parent to eth0
        result = runner.run(
            'interfaces update -i %s -p %s' % (child_id, parent_id)
        )
        assert result.exit_code == 0

        # Verify parent: eth0:1 parent should be eth0
        result = runner.run('interfaces list -p %s' % parent_id)
        assert result.exit_code == 0
        assert 'eth0:1' in result.output

        # Update name, mac_address, type, speed
        result = runner.run(
            "interfaces update -i %s -n child -m 3 -t 161 -S 12345678" %
            child_id
        )
        assert result.exit_code == 0

        # Verify name and mac_address updated
        result = runner.run('interfaces list -n child')  # Lookup by new name
        assert result.exit_code == 0
        expected = (
            '161',  # type
            '12345678',  # speed
            '00:00:00:00:00:03'  # mac_address
        )
        for e in expected:
            assert e in result.output

        # Test addresses  - We know they will be empty
        # FIXME(jathan): Once we have a better story about differential
        # assignment of addresses to interfaces, make it so that addresses can
        # be persistent on updates.
        result = runner.run('interfaces list -i %s' % parent_id)
        assert result.exit_code == 0
        assert '10.10.10.1/32' not in result.output

        # So let's add it back and verify...
        runner.run(
            'interfaces update -i %s -c 10.10.10.1/32' % parent_id
        )
        result = runner.run('interfaces list -i %s' % parent_id)
        assert result.exit_code == 0
        assert '10.10.10.1/32' in result.output

        # Test description.
        # FIXME(jathan): It doesn't currently show in the CLI output. So we're
        # just making sure it doesn't fail.
        result = runner.run(
            "interfaces update -i %s -e 'description'" % child_id
        )
        assert result.exit_code == 0


def test_interfaces_remove(site_client, device, interface):
    """Test ``nsot interfaces remove``."""
    runner = CliRunner(site_client.config)
    with runner.isolated_filesystem():
        # Just delete the interface we have.
        result = runner.run('interfaces remove -i %s' % interface['id'])
        assert result.exit_code == 0
        assert 'Removed interface!' in result.output


def test_interfaces_remove_by_natural_key(site_client, device, interface):
    """Test ``nsot interfaces remove`` via the natural key."""
    runner = CliRunner(site_client.config)
    with runner.isolated_filesystem():
        # Just delete the interface we have, but by natural key this time.
        identifier = '%s:%s' % (device['hostname'], interface['name'])
        result = runner.run('interfaces remove -i %s' % identifier)
        assert result.exit_code == 0
        assert 'Removed interface!' in result.output


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
