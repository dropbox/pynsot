# -*- coding: utf-8 -*-

"""
Test Circuits in the CLI app.
"""

from __future__ import absolute_import, unicode_literals
import logging

from tests.fixtures import (attribute, client, config, device, interface,
                            network, runner, site, site_client)
from tests.fixtures.circuits import (circuit, circuit_attributes, device_a,
                                     device_z, interface_a, interface_z)
from tests.util import assert_output, assert_outputs


log = logging.getLogger(__name__)


def test_circuits_add(runner, interface_a, interface_z):
    """ Test adding a normal circuit """

    with runner.isolated_filesystem():
        # Add a circuit with interfaces on each end
        result = runner.run(
            'circuits add -A {0} -Z {1} -n add_test1'.format(
                interface_a['id'],
                interface_z['id']
            )
        )
        assert_output(result, ['Added circuit!'])

        # Verify the circuit was created by listing
        result = runner.run('circuits list')
        assert_output(result, ['add_test1'])


def test_circuits_add_single_sided(runner, interface_a):
    """ Add a circuit with no remote end """

    with runner.isolated_filesystem():
        result = runner.run(
            'circuits add -A {0} -n add_test2'.format(interface_a['id'])
        )

        assert_output(result, ['Added circuit!'])

        result = runner.run('circuits list')
        assert_output(result, ['add_test2'])


def test_circuits_add_intf_reuse(runner, interface_a):
    """
    Try creating two circuits with the same interface, which should fail
    """

    with runner.isolated_filesystem():
        cmd = 'circuits add -A {0} -n {1}'

        result = runner.run(cmd.format(interface_a['id'], 'circuit1'))
        assert result.exit_code == 0

        result = runner.run(cmd.format(interface_a['id'], 'bad_circuit'))
        assert result.exit_code != 0
        assert 'endpoint_a:  This field must be unique' in result.output


def test_circuits_add_dupe_name(runner, interface_a, interface_z):
    """
    Try creating two circuits with the same name, which should fail
    """

    with runner.isolated_filesystem():
        cmd = 'circuits add -A {0} -n foo'

        result = runner.run(cmd.format(interface_a['id']))
        assert result.exit_code == 0

        result = runner.run(cmd.format(interface_z['id']))
        assert result.exit_code != 0
        assert 'circuit with this name already exists' in result.output


def test_circuits_list(runner, circuit):
    """ Make sure we can list out a circuit """

    circuit_name = 'test_circuit'

    with runner.isolated_filesystem():
        result = runner.run('circuits list')
        assert_output(result, [circuit_name])

        result = runner.run('circuits list -i {}'.format(circuit_name))
        assert_output(result, [circuit_name])


def test_circuits_list_nonexistant(runner):
    """ Listing a non-existant circuit should fail """

    with runner.isolated_filesystem():
        result = runner.run('circuits list -i nopenopenope')

        assert result.exit_code != 0
        assert 'No such Circuit found' in result.output


def test_circuits_list_natural_key_output(runner, circuit):
    """ Natural key output should just list the circuit names """

    with runner.isolated_filesystem():
        result = runner.run('circuits list -N')

        assert result.exit_code == 0
        assert result.output == "test_circuit\n"


def test_circuits_list_grep_output(runner, circuit):
    """ grep output should list circuit names with all the attributes """

    expected_output = (
        "test_circuit owner=alice\n"
        "test_circuit vendor=lasers go pew pew\n"
    )

    with runner.isolated_filesystem():
        result = runner.run('circuits list -g')

        assert result.exit_code == 0
        assert result.output == expected_output


def test_circuits_list_addresses(runner, circuit, interface_a, interface_z):
    """ Test listing out a circuit's interface addresses """

    with runner.isolated_filesystem():
        result = runner.run('circuits list -i {} addresses'.format(
            circuit['id']
        ))

        assert_outputs(
            result,
            [
                [interface_a['addresses'][0].split('/')[0]],
                [interface_z['addresses'][0].split('/')[0]]
            ]
        )


def test_circuits_list_devices(runner, circuit, device_a, device_z):
    """ Test listing out a circuit's devices """

    with runner.isolated_filesystem():
        result = runner.run('circuits list -i {} devices'.format(
            circuit['id']
        ))

        assert_outputs(
            result,
            [
                [device_a['hostname']],
                [device_z['hostname']]
            ]
        )


def test_circuits_list_interfaces(runner, circuit, interface_a, interface_z):
    """ Test listing out a circuit's interfaces """

    with runner.isolated_filesystem():
        result = runner.run('circuits list -i {} interfaces'.format(
            circuit['id']
        ))

        assert_outputs(
            result,
            [
                [interface_a['device_hostname'], interface_a['name']],
                [interface_z['device_hostname'], interface_z['name']]
            ]
        )


def test_circuits_remove(runner, circuit):
    """ Make sure we can remove an existing circuit """

    circuit_name = 'test_circuit'

    with runner.isolated_filesystem():
        result = runner.run('circuits remove -i {}'.format(circuit_name))
        assert result.exit_code == 0


def test_circuits_update_name(runner, circuit):
    """ Test update by changing the circuit name """

    old_name = 'test_circuit'
    new_name = 'awesome_circuit'

    with runner.isolated_filesystem():
        result = runner.run('circuits update -i {} -n {}'.format(
            old_name,
            new_name
        ))
        assert result.exit_code == 0

        # Make sure we can look up the circuit by its new name
        result = runner.run('circuits list -i {}'.format(new_name))
        assert_output(result, [new_name])

        # Make sure the old name doesn't exist
        result = runner.run('circuits list -i {}')
        assert result.exit_code != 0
        assert 'No such Circuit found' in result.output


def test_circuits_update_interface(runner, circuit, interface):
    """ Test updating a circuit's Z side interface """

    with runner.isolated_filesystem():
        result = runner.run('circuits update -i {0} -Z {1}'.format(
            circuit['name'], interface['id']
        ))
        assert_output(result, ['Updated circuit!'])
