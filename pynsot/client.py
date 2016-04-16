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

from __future__ import unicode_literals
import getpass
import json
import logging
import os

from .vendor import click
from .vendor.requests.auth import AuthBase
from .vendor import slumber
from .vendor.slumber.exceptions import HttpClientError

from .util import get_result
from . import constants, dotfile


__author__ = 'Jathan McCollum'
__maintainer__ = 'Jathan McCollum'
__email__ = 'jathan@dropbox.com'
__copyright__ = 'Copyright (c) 2015-2016 Dropbox, Inc.'


# Logger
log = logging.getLogger(__name__)


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
    authentication_class = None

    def __init__(self, base_url=None, **kwargs):
        self._base_url = base_url
        auth = kwargs.pop('auth', None)  # Ditch default auth
        self.default_site = kwargs.pop('default_site', None)  # Default site_id
        self.api_version = kwargs.pop('api_version', None)  # API version
        log.debug('Using api_version = %s' % self.api_version)

        # Override the auth method if we have defined .get_auth()
        if auth is None:
            # Set these as object attributes so that they can be mutated in the
            # subclass. We want subclasses to be able to pop items off of the
            # kwargs before they're passed to BaseClient.
            self._kwargs = kwargs
            auth = self.get_auth(client=self)

        kwargs['auth'] = auth
        kwargs['append_slash'] = True  # Append slashes!
        super(BaseClient, self).__init__(base_url, **kwargs)

        # Store auth and headers for use later.
        self._auth = auth
        self._headers = self._store['session'].headers

    def _fetch_resources(self):
        """Fetch resources from API"""
        headers = self._headers
        auth = self._auth
        api_root = self._base_url + '/'
        r = slumber.requests.get(api_root, auth=auth, headers=headers)

        if r.ok:
            return r.json()
        else:
            msg = r.json().get(
                'error', 'Error fetching API resources. Is auth OK?'
            )
            raise ClientError(msg)

    def _populate_resources(self, resources=None):
        """
        Use `resources` to populate ... resources.

        :param resources:
            A list or dict containing resource names
        """
        if resources is None:
            raise TypeError('Resources must be iterable')

        # Iterate the resource names, and set a local attribute name using the
        # resource method we retrieved from the API.
        for resource_name in resources:
            resource = getattr(self, resource_name)
            setattr(self, resource_name, resource)

    def get_auth(self, **kwargs):
        """
        Subclasses should references kwargs from ``self._kwargs``.

        :param client:
            Client instance. Defaults to ``self``.
        """
        if self.authentication_class is None:
            raise NotImplementedError(
                'Define authentication_class in a subclass!'
            )

        client = kwargs.get('client')
        return self.authentication_class(client=client)

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


class BaseClientAuth(AuthBase):
    def __init__(self, client):
        """
        Any subclasses must accept ``client`` as the first argument. Kwargs
        come from the client so that they can be mutated and will be available
        as ``self.kwargs`` on authentication subclasses.

        Additionally, you must also subclass ``__call__``.
        """
        self.client = client
        self.base_url = client._base_url
        self.api_version = client.api_version
        self.kwargs = client._kwargs

    def append_api_version(self, request):
        """Append API version into Accept header."""
        headers = request.headers
        accept_header = headers.get('accept')

        # If the header exists
        if accept_header:
            version_value = ';version={}'.format(self.api_version)
            headers['accept'] += version_value

    def __call__(self, r):
        if self.api_version is not None:
            self.append_api_version(r)

        return r


class EmailHeaderAuthentication(BaseClientAuth):
    """Special authentication that sets the email auth header."""

    def __init__(self, client):
        super(EmailHeaderAuthentication, self).__init__(client)
        email = self.kwargs.pop('email', None)
        default_domain = self.kwargs.pop('default_domain', 'localhost')
        auth_header = self.kwargs.pop('auth_header', constants.AUTH_HEADER)

        if email is None and default_domain:
            log.debug('No email provided; Using default_domain: %r',
                      default_domain)
            user = self.get_user()
            email = '%s@%s' % (user, default_domain)
            log.debug('Using email: %r', email)

        if email is not None and '@' not in email:
            raise LoginFailed('You must provide an email!')

        self.email = email
        self.auth_header = auth_header

    @classmethod
    def get_user(cls):
        """Get the local username, or if root, the sudo username."""
        user = getpass.getuser()
        if user == 'root':
            user = os.getenv('SUDO_USER')
        return user

    def __call__(self, r):
        """Set the auth header."""
        r = super(EmailHeaderAuthentication, self).__call__(r)
        r.headers[self.auth_header] = self.email
        return r


class EmailHeaderClient(BaseClient):
    """Default client using email auth header method."""
    authentication_class = EmailHeaderAuthentication
    required_arguments = ('email', 'default_domain', 'auth_header')


class AuthTokenAuthentication(BaseClientAuth):
    """
    Special authentication that utilizes auth_tokens.

    Adds header for "Authorization: ApiToken {email}:{auth_token}"
    """
    def __init__(self, client):
        super(AuthTokenAuthentication, self).__init__(client)
        kwargs = self.kwargs
        base_url = self.base_url
        email = kwargs.pop('email', None)
        secret_key = kwargs.pop('secret_key', None)

        self.email = email
        self.auth_token = self.get_token(base_url, email, secret_key)

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
            url = base_url + '/authenticate/'
            headers = {'content-type': 'application/json'}
            resp = slumber.requests.post(
                url, data=json.dumps(data), headers=headers
            )
        except Exception as err:
            log.debug('Got error: %s' % (err,))
            self.client.error(err)

        if resp.ok:
            log.debug('Got response: %r' % (resp,))
            result = get_result(resp)['auth_token']
            return result
        else:
            msg = 'Failed to fetch auth_token from %s' % base_url
            err = HttpClientError(msg, response=resp, content=resp.content)
            self.client.error(err)

    def __call__(self, r):
        r = super(AuthTokenAuthentication, self).__call__(r)
        header = 'AuthToken %s:%s' % (self.email, self.auth_token)
        r.headers['Authorization'] = header
        return r


class AuthTokenClient(BaseClient):
    """Client that uses auth_token method."""
    authentication_class = AuthTokenAuthentication
    required_arguments = ('email', 'secret_key')


#: Mapping to our two (2) hard-coded auth methods
AUTH_CLIENTS = {
    'auth_header': EmailHeaderClient,
    'auth_token': AuthTokenClient,
}

#: Default client class
Client = AUTH_CLIENTS[constants.DEFAULT_AUTH_METHOD]


def get_auth_client_info(auth_method):
    """
    Return the proper Client class and required args.

    :param auth_method:
        Auth method used by the client
    """
    return AUTH_CLIENTS[auth_method]


def get_api_client(auth_method=None, url=None, extra_args=None,
                   use_dotfile=True):
    """
    Safely create an API client so that users don't see tracebacks.

    Any arguments taht aren't explicitly passed will be replaced by the
    contents of the user's dotfile.

    :param auth_method:
        Auth method used by the client

    :param url:
        API URL

    :param extra_args:
        Dict of extra keyword args to be passed to the API client class

    :param use_dotfile:
        Whether to read the dotfile or not.
    """
    if extra_args is None:
        extra_args = {}

    # Should we read the dotfile? If not, client_args will be an empty dict
    if use_dotfile:
        try:
            log.debug('Reading dotfile.')
            client_args = dotfile.Dotfile().read()
        except dotfile.DotfileError as err:
            raise click.UsageError(err.message)
    else:
        client_args = {}

    # Merge the extra_args w/ the client_args from the config
    client_args.update(extra_args)

    # Minimum required arguments that we don't want getting passed to the
    # client
    if auth_method is None:
        auth_method = client_args.pop('auth_method')
    if url is None:
        url = client_args.pop('url')

    # Validate the auth_method
    log.debug('Validating auth_method: %s', auth_method)
    try:
        client_class = get_auth_client_info(auth_method)
    except KeyError:
        raise click.UsageError('Invalid auth_method: %s' % (auth_method,))

    arg_names = client_class.required_arguments

    # Allow optional arguments in arg_names
    optional_args = tuple(constants.OPTIONAL_FIELDS)
    arg_names += optional_args

    # Remove non-relavant args
    for client_arg in client_args.keys():
        if client_arg not in arg_names:
            log.debug(
                'Skipping %r in config for auth_method %r' % (
                    client_arg, auth_method
                )
            )
            client_args.pop(client_arg)

    try:
        api_client = client_class(url, **client_args)
    except ClientError as err:
        msg = str(err)
        if 'Connection refused' in msg:
            msg = 'Could not connect to server: %s' % (url,)
        raise click.UsageError(msg)

    return api_client
