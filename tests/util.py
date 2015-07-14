# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""
Utilities for testing.
"""


import contextlib
import logging
import os
import requests_mock
import shutil
import sys
import tempfile

from pynsot import dotfile
from pynsot.vendor import click
from pynsot.vendor.click.testing import CliRunner as BaseCliRunner


log = logging.getLogger(__name__)


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

    @contextlib.contextmanager
    def isolated_requests(self):
        """
        A context manager that mocks requests in an isolated filesystem.
        """
        with requests_mock.Mocker() as mock, self.isolated_filesystem():
            yield mock
