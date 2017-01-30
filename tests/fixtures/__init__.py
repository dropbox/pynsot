# -*- coding: utf-8 -*-

"""
Make dummy data and fixtures and stuff.
"""

from __future__ import unicode_literals
import logging
import os

import pytest
from pytest_django.fixtures import live_server, django_user_model

from pynsot.client import get_api_client
from tests.util import CliRunner


__all__ = ('django_user_model', 'live_server')


# Logger
log = logging.getLogger(__name__)

# API version to use for the API client
API_VERSION = os.getenv('NSOT_API_VERSION')

# Dummy config data used for testing auth_header authentication.
AUTH_HEADER_CONFIG = {
    'auth_method': 'auth_header',
    'default_domain': 'localhost',
    'auth_header': 'X-NSoT-Email',
}

# This is used to test dotfile settings.
DOTFILE_CONFIG_DATA = {
    'auth_token': {
        'email': 'jathan@localhost',
        'url': 'http://localhost:8990/api',
        'auth_method': 'auth_token',
        'secret_key': 'MJMOl9W7jqQK3h-quiUR-cSUeuyDRhbn2ca5E31sH_I=',
    },
    'auth_header': {
        'email': 'jathan@localhost',
        'url': 'http://localhost:8990/api',
        'auth_method': 'auth_header',
        'default_domain': 'localhost',
        'auth_header': 'X-NSoT-Email',
    }
}


@pytest.fixture
def config(live_server, django_user_model):
    """Create a user and return an auth_token config matching that user."""
    user = django_user_model.objects.create(
        email='jathan@localhost', is_superuser=True, is_staff=True
    )
    data = {
        'email': user.email,
        'secret_key': user.secret_key,
        'auth_method': 'auth_token',
        'url': live_server.url + '/api',
        # 'api_version': API_VERSION,
        'api_version': '1.0',  # Hard-coded.
    }

    return data


@pytest.fixture
def auth_header_config(config):
    """Return an auth_header config."""
    config.pop('secret_key')
    config.update(AUTH_HEADER_CONFIG)
    return config


@pytest.fixture
def client(config):
    """Create and return an admin client."""
    api = get_api_client(extra_args=config, use_dotfile=False)
    api.config = config
    return api


@pytest.fixture
def site(client):
    """Returns a Site object."""
    return client.sites.post({'name': 'Foo', 'description': 'Foo site.'})


@pytest.fixture
def site_client(client, site):
    """Returns a client tied to a specific site."""
    client.config['default_site'] = site['id']
    client.default_site = site['id']
    return client


@pytest.fixture
def runner(site_client):
    return CliRunner(site_client.config)


@pytest.fixture
def attribute(site_client):
    """Return an Attribute object."""
    return site_client.sites(site_client.default_site).attributes.post(
        {'name': 'foo', 'resource_name': 'Device'}
    )


@pytest.fixture
def device(site_client):
    """Return a Device object."""
    return site_client.sites(site_client.default_site).devices.post(
        {'hostname': 'foo-bar1'}
    )


@pytest.fixture
def network(site_client):
    """Return a Network object."""
    return site_client.sites(site_client.default_site).networks.post(
        {'cidr': '10.20.30.0/24'}
    )


@pytest.fixture
def interface(site_client, device, network):
    """
    Return an Interface object.

    Interface is bound to ``device`` with an address assigned from ``network``.
    """
    device_id = device['id']
    return site_client.sites(site_client.default_site).interfaces.post(
        {'name': 'eth0', 'addresses': ['10.20.30.1/32'], 'device': device_id}
    )
