# -*- coding: utf-8 -*-

"""
Simple Python API client for NSoT REST API.

The easiest way to get a client is to call ``get_api_client()`` with no
arguments. This will read the user's ``~/.pynsotrc`` file and pass the values
to the client constructor::

    >>> from pynsot.client import get_api_client
    >>> api = get_api_client()
    >>> api
    AuthTokenClient(url=http://localhost:8990/api)>
"""

__author__ = 'Jathan McCollum'
__maintainer__ = 'Jathan McCollum'
__email__ = 'jathan@dropbox.com'
__copyright__ = 'Copyright (c) 2015 Dropbox, Inc.'


import getpass
import json
import logging
import os

from .vendor import click
from .vendor.requests.auth import AuthBase
from .vendor import slumber
from .vendor.slumber.exceptions import HttpClientError

from . import dotfile


# Logger
log = logging.getLogger(__name__)

# Header used for passthrough authentication.
AUTH_HEADER = 'X-NSoT-Email'


__all__ = (
    'ClientError', 'LoginFailed', 'BaseClient', 'EmailHeaderAuthentication',
    'EmailHeaderClient', 'AuthTokenAuthentication', 'AuthTokenClient',
    'get_auth_client_info', 'get_api_client'
)


class ClientError(HttpClientError):
    """Generic client error."""


class LoginFailed(ClientError):
    """Raised when login fails for some reason."""


class BaseClient(slumber.API):
    """
    Magic REST API client for NSoT.
    """
    def __init__(self, base_url=None, **kwargs):
        auth = kwargs.pop('auth', None)  # Ditch default auth
        self.default_site = kwargs.pop('default_site', None)  # Default site_id

        # Override the auth method if we have defined .get_auth()
        if auth is None:
            # Set these as object attributes so that they can be mutated in the
            # subclass .get_auth() method
            self._kwargs = kwargs
            auth = self.get_auth(base_url)

        kwargs['auth'] = auth
        kwargs['append_slash'] = False  # No slashes!
        super(BaseClient, self).__init__(base_url, **kwargs)

    def get_auth(self, base_url=None):
        """
        Subclasses should references kwargs from ``self._kwargs``.

        :param base_url:
            Base API URL
        """
        raise NotImplementedError('SUBCLASS ME OR SOMETHING!')

    def error(self, exc):
        """
        Take errors and make them human-readable.

        :param exc:
            Exception instance
        """
        log.debug('Processing error: %r' % (exc,))
        # If it's a HTTP response, format the JSON
        try:
            try:
                err = exc.response.json()['error']
            except ValueError:
                # This is probably a JSON decoding error
                msg = exc.message
            else:
                msg = '%s %s' % (err['code'], err['message'])
        except AttributeError:
            msg = str(exc)
        raise ClientError(msg)

    def get_resource(self, resource_name):
        """
        Return a single resource object.

        :param resource_name:
            Name of resource
        """
        return getattr(self, resource_name)

    def __repr__(self):
        cls_name = self.__class__.__name__
        return '<%s(url=%s)>' % (cls_name, self._store['base_url'])


class EmailHeaderAuthentication(AuthBase):
    """Special authentication that sets the email auth header."""
    def __init__(self, email=None, auth_header=AUTH_HEADER):
        if email is None:
            raise LoginFailed('You must provide an email!')
        self.email = email
        self.auth_header = auth_header

    def __call__(self, r):
        """Set the auth header."""
        r.headers[self.auth_header] = self.email
        return r


class EmailHeaderClient(BaseClient):
    """Default client using email auth header method."""
    @classmethod
    def get_user(cls):
        """Get the local username, or if root, the sudo username."""
        user = getpass.getuser()
        if user == 'root':
            user = os.getenv('SUDO_USER')
        return user

    def get_auth(self, base_url):
        kwargs = self._kwargs
        email = kwargs.pop('email', None)
        default_domain = kwargs.pop('default_domain', 'localhost')

        if email is None and default_domain:
            log.debug('No email provided; Using default_domain: %r',
                      default_domain)
            user = self.get_user()
            email = '%s@%s' % (user, default_domain)
            log.debug('Using email: %r', email)

        auth_header = kwargs.pop('auth_header', AUTH_HEADER)
        return EmailHeaderAuthentication(email, auth_header)


class AuthTokenAuthentication(AuthBase):
    """
    Special authentication that utilizes auth_tokens.

    Adds header for "Authorization: ApiToken {email}:{auth_token}"
    """
    def __init__(self, email=None, auth_token=None):
        self.email = email
        self.auth_token = auth_token

    def __call__(self, r):
        header = 'AuthToken %s:%s' % (self.email, self.auth_token)
        r.headers['Authorization'] = header
        return r


class AuthTokenClient(BaseClient):
    """Client that uses auth_token method."""
    def get_token(self, base_url, email, secret_key):
        """
        Currently ghetto: Hit the API to get an auth_token.

        :param base_url:
            API URL

        :param email:
            User's email

        :param secret_key:
            User's secret_key
        """
        data = {'email': email, 'secret_key': secret_key}
        debug_data = data.copy()  # For debug display
        debug_data['secret_key'] = 'X' * 8

        log.debug('Getting token for user data: %r' % (debug_data,))
        try:
            url = base_url + '/authenticate'
            headers = {'content-type': 'application/json'}
            r = slumber.requests.post(url, data=json.dumps(data),
                                      headers=headers)
        except Exception as err:
            log.debug('Got error: %s' % (err,))
            self.error(err)

        if r.ok:
            log.debug('Got response: %r' % (r,))
            return r.json()['data']['auth_token']
        else:
            msg = 'Failed to fetch auth_token from %s' % base_url
            err = HttpClientError(msg, response=r, content=r.content)
            self.error(err)

    def get_auth(self, base_url):
        kwargs = self._kwargs
        email = kwargs.pop('email', None)
        secret_key = kwargs.pop('secret_key', None)
        auth_token = self.get_token(base_url, email, secret_key)
        auth = AuthTokenAuthentication(email, auth_token)
        return auth
Client = AuthTokenClient  # Default client is auth_token


# Mapping to our two (2) hard-coded auth methods and their required arguments.
AUTH_CLIENTS = {
    'auth_header': (EmailHeaderClient, ('email', 'default_domain', 'default_site')),
    'auth_token': (AuthTokenClient, ('email', 'secret_key', 'default_site')),
}


def get_auth_client_info(auth_method):
    """
    Return the proper Client class and required args.

    :param auth_method:
        Auth method used by the client
    """
    return AUTH_CLIENTS[auth_method]


def get_api_client(auth_method=None, url=None, extra_args=None):
    """
    Safely create an API client so that users don't see tracebacks.

    Any arguments taht aren't explicitly passed will be replaced by the
    contents of the user's dotfile.

    :param auth_method:
        Auth method used by the client

    :param url:
        API URL
    """
    if extra_args is None:
        extra_args = {}

    # Read the dotfile
    try:
        log.debug('Reading dotfile.')
        client_args = dotfile.Dotfile().read()
    except dotfile.DotfileError as err:
        raise click.UsageError(err.message)

    # Merge the extra_args w/ the client_args from the config
    client_args.update(extra_args)

    # Minimum required arguments that we don't want getting passed to the client
    auth_method = client_args.pop('auth_method')
    url = client_args.pop('url')

    # Validate the auth_method
    log.debug('Validating auth_method: %s', auth_method)
    try:
        client_class, arg_names = get_auth_client_info(auth_method)
    except KeyError:
        raise click.UsageError('Invalid auth_method: %s' % (auth_method,))

    try:
        api_client = client_class(url, **client_args)
    except ClientError as err:
        msg = str(err)
        if 'Connection refused' in msg:
            msg = 'Could not connect to server: %s' % (url,)
        raise click.UsageError(msg)
    return api_client
