# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""
Test the API client.
"""

import json
import logging
import os
import pytest
import requests
import requests_mock
import shlex

from pynsot import client
from pynsot.vendor import click
from pynsot.vendor.click.testing import CliRunner

from .fixtures import config, API_URL, AUTH_RESPONSE, SITES_RESPONSE


@requests_mock.Mocker()
class Server(object):
    def __init__(self, base_url=API_URL):
        self.base_url = base_url

    def test_authenticate(self, m):
        uri = self.base_url + '/authenticate/'
        m.register_uri('POST', uri, json=AUTH_RESPONSE)
        return requests.post(uri).text


def test_authentication(config):
    auth = {'email': config['email'], 'secret_key': config['secret_key']}
    url = config['url'] + '/authenticate/'
    payload = json.dumps(auth)

    with requests_mock.Mocker() as mock:
        mock.post(url, json=AUTH_RESPONSE)
        resp = requests.post(url, data=payload)

        assert resp.status_code == 200
        assert 'auth_token' in resp.json()['data']


def test_sites(config):
    headers = {'Content-Type': 'application/json'}
    url = config['url'] + '/sites/'
    auth = {'email': config['email'], 'secret_key': config['secret_key']}
    payload = json.dumps(auth)

    with requests_mock.Mocker() as mock:
        # Mock authentication
        auth_url = config['url'] + '/authenticate/'
        mock.post(auth_url, json=AUTH_RESPONSE, headers=headers)
        api = client.AuthTokenClient(
            config['url'],
            email=config['email'],
            secret_key=config['secret_key']
        )

        # Mock sites response
        mock.get(url, json=SITES_RESPONSE, headers=headers)
        resp = api.sites.get()

        assert resp['data']['total'] == 1
