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
    DEVICE_RETRIEVE, DEVICE_UPDATE
)


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
        cwd = os.getcwd()
        t = tempfile.mkdtemp()
        os.chdir(t)
        rcfile = dotfile.Dotfile('.pynsotrc')
        rcfile.write(self.client_config)
        try:
            yield t
        finally:
            os.chdir(cwd)
            try:
                shutil.rmtree(t)
            except (OSError, IOError):
                pass


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


def test_devices_list(config):
    """Test ``nsot devices list -s 1``"""
    headers = {'Content-Type': 'application/json'}
    auth_url = config['url'] + '/authenticate/'
    devices_url = config['url'] + '/sites/1/devices/'

    runner = CliRunner(config)
    with requests_mock.Mocker() as mock, runner.isolated_filesystem():
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        mock.get(devices_url, json=DEVICES_RESPONSE, headers=headers)

        result = runner.invoke(app, shlex.split('devices list -s 1'))
        assert result.exit_code == 0


def test_device_update(config):
    """Test ``nsot devices update -s 1``"""
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
        # import pdb; pdb.set_trace()
        assert result.exit_code == 0

        expected_output = (
            "[SUCCESS] Updated device with args: attributes={'monitored':"
            " ''}, hostname=None!\n"
        )
        # import pdb; pdb.set_trace()
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
