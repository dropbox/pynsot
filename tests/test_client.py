# -*- coding: utf-8 -*-

"""
Test the API client.
"""

from __future__ import unicode_literals
import logging
import pytest

from pynsot.util import get_result
from .fixtures import config, client


__all__ = ('client', 'config', 'pytest')


log = logging.getLogger(__name__)


def test_authentication(client):
    """Test manual client authentication."""
    auth = {
        'email': client.config['email'],
        'secret_key': client.config['secret_key']
    }
    # Good
    resp = client.authenticate.post(auth)
    result = get_result(resp)
    assert 'auth_token' in result


def test_sites(client):
    """Test working with sites using the client."""
    site = client.sites.post({'name': 'Foo'})
    assert client.sites.get() == [site]
    assert client.sites(site['id']).get() == site
