# -*- coding: utf-8 -*-

"""
Simple Python API client for NSoT REST API
"""

__author__ = 'Jathan McCollum'
__maintainer__ = 'Jathan McCollum'
__email__ = 'jathan@dropbox.com'
__copyright__ = 'Copyright (c) 2015 Dropbox, Inc.'


import json
import logging
from requests.auth import AuthBase
import slumber
from slumber.exceptions import HttpClientError


# Logger
log = logging.getLogger(__name__)

# Header used for passthrough authentication.
AUTH_HEADER = 'X-NSoT-Email'


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
            err = exc.response.json()['error']
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
    def get_auth(self, base_url):
        kwargs = self._kwargs
        email = kwargs.pop('email', None)
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
        log.debug('Getting token for user data: %r' % (data,))
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
            msg = 'Failed to fetch auth_token'
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
    'auth_header': (EmailHeaderClient, ('email', 'default_site')),
    'auth_token': (AuthTokenClient, ('email', 'secret_key', 'default_site')),
}


def get_auth_client_info(auth_method):
    """
    Return the proper Client class and required args.

    :param auth_method:
        Auth method used by the client
    """
    return AUTH_CLIENTS[auth_method]
