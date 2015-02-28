# -*- coding: utf-8 -*-

"""
Base CLI commands for all objects. Model-specific objects and argument parsers
will be defined in subclasses or by way of factory methods.
"""

__author__ = 'Jathan McCollum'
__maintainer__ = 'Jathan McCollum'
__email__ = 'jathan@dropbox.com'
__copyright__ = 'Copyright (c) 2015 Dropbox, Inc.'


import click
import logging
import os
from slumber.exceptions import HttpClientError
import sys
import tabulate

import pynsot
from . import client, dotfile
from .models import ApiModel


# Constants/Globals
if os.getenv('DEBUG'):
    logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

# We want no padding on the table columns
tabulate.MIN_PADDING = 0

# Make the --help option also have -h
CONTEXT_SETTINGS = {
    'help_option_names': ['-h', '--help'],
}

# Mapping to our two (2) hard-coded auth methods for now.
AUTH_CLIENTS = {
    'auth_header': client.EmailHeaderClient,
    'auth_token': client.AuthTokenClient,
}

# Where to find the command plugins.
CMD_FOLDER = os.path.abspath(os.path.join(
                             os.path.dirname(__file__), 'commands'))


class NsotCLI(click.MultiCommand):
    """
    Base command object used to define object-specific command-line parsers.

    This will load command plugins from the "commands" folder.

    Plugins must be named "cmd_{foo}.py".
    """
    def list_commands(self, ctx):
        """List all commands from python modules in plugin folder."""
        rv = []
        for filename in os.listdir(CMD_FOLDER):
            if filename.endswith('.py') and filename.startswith('cmd_'):
                rv.append(filename[4:-3])
        rv.sort()
        return rv

    def get_command(self, ctx, name):
        """Import a command module and return it."""
        try:
            if sys.version_info[0] == 2:
                name = name.encode('ascii', 'replace')
            mod = __import__('pynsot.commands.cmd_' + name,
                             None, None, ['app'])
        except ImportError as err:
            print err
            return None
        return mod.cli


class App(object):
    """Context object for holding state data for the CLI app."""
    def __init__(self, client_args, ctx, verbose=False):
        self.client_args = client_args
        self.ctx = ctx
        self.verbose = verbose
        self.resource_name = self.ctx.invoked_subcommand

    def get_api_client(self, auth_method=None, url=None, email=None,
                       secret_key=None):
        """
        Safely create an API client so that users don't see tracebacks.

        :param auth_method:
            Auth method used by the client

        :param url:
            API URL

        :param email:
            User's email

        :param secret_key:
            User's secret_key
        """
        try:
            client_class, arg_names = client.get_auth_client_info(auth_method)
        except KeyError:
            raise click.UsageError('Invalid auth_method: %s' % (auth_method,))

        # Construct kwargs to pass to the client_class
        local_vars = locals()
        kwargs = {arg_name: local_vars[arg_name] for arg_name in arg_names}
        try:
            api_client = client_class(url, **kwargs)
        except client.ClientError as err:
            msg = str(err)
            if 'Connection refused' in msg:
                msg = 'Could not connect to server: %s' % (url,)
            raise click.UsageError(msg)
        return api_client

    @property
    def api(self):
        """This way the API client is not created until called."""
        if not hasattr(self, '_api'):
            self._api = self.get_api_client(**self.client_args)
        return self._api

    @property
    def singular(self):
        """Return singular form of resource_name. (e.g. "sites" -> "site")"""
        resource_name = self.resource_name
        if resource_name.endswith('s'):
            resource_name = resource_name[:-1]
        return resource_name

    @property
    def resource(self):
        """
        Return an API resource method for calling endpoints.

        For example if ``resource_name`` is ``networks``, this is equivalent to
        calling ``self.api.networks``.
        """
        return self.api.get_resource(self.resource_name)

    @staticmethod
    def pretty_dict(data, sep=', '):
        """
        Return a dict in k=v format.

        :param dict:
            A dict

        :param sep:
            Character used to separate items
        """
        pretty = sep.join('%s=%r' % (k, v) for k, v in data.iteritems())
        return pretty

    def format_message(self, obj_single, message):
        """Attempt to make messages human-readable."""
        if 'UNIQUE constraint failed' in message:
            message = '%s object already exists.' % (obj_single.title(),)
        return message

    def handle_error(self, action, data, err):
        """
        Handle error API response.

        :param action:
            The action name

        :param data:
            Dict of arguments

        :param err:
            Exception object
        """
        resp = getattr(err, 'response', None)
        obj_single = self.singular
        extra = '\n'

        # If it's an API error, format it all pretty-like for human eyes.
        if resp is not None:
            body = resp.json()

            msg = body['error']['message']
            msg = self.format_message(obj_single, msg)

            # Add the status code and reason to the output
            if self.verbose:
                t_ = '%s %s'
                reason = resp.reason.upper()
                extra += t_ % (resp.status_code, reason)
        else:
            msg = str(err)

        # If we're being verbose, print some extra context.
        if self.verbose:
            t_ = ' trying to %s %s with args: %s'
            pretty_dict = self.pretty_dict(data)
            extra += t_ % (action, obj_single, pretty_dict)
            msg += extra

        # Colorize the failure text as red.
        self.ctx.exit(click.style('[FAILURE] ', fg='red') + msg)

    def handle_response(self, action, data, result):
        """
        Handle positive API response.

        :param action:
            The action name

        :param data:
            Dict of arguments

        :param result:
            Dict containing result
        """
        pretty_dict = self.pretty_dict(data)
        t_ = '%s %s with args: %s!'
        if action.endswith('e'):
            action = action[:-1]  # "remove" -> "remov"
        action = action.title() + 'ed'  # "remove" -> "removed"
        msg = t_ % (action, self.singular,  pretty_dict)

        # Colorize the success text as green.
        click.echo(click.style('[SUCCESS] ', fg='green') + msg)

    def map_fields(self, fields, fields_map):
        """
        Map ``fields`` using ``fields_map`` for table display.

        :param fields:
            List of field names

        :param fields_map:
            Mapping of field names to translations
        """
        log.debug('MAP_FIELDS FIELDS = %r' % (fields,))
        log.debug('MAP_FIELDS FIELDS_MAP = %r' % (fields_map,))
        try:
            headers = [fields_map[f] for f in fields]
        except KeyError as err:
            msg = 'Could not map field %s when displaying results.' % (err,)
            self.ctx.exit(msg)
        return headers

    def print_list(self, objects, display_fields):
        """
        Print a list of objects in a table format.

        :param objects:
            List of object dicts

        :param display_fields:
            Ordered list of 2-tuples of (field, display_name) used
            to translate field names for display
        """
        # Extract the field names and create a mapping used for translation
        fields = [f[0] for f in display_fields]  # Field names are 1st item
        fields_map = dict(display_fields)

        # Human-readable field headings as they will be displayed
        tablefmt = 'simple'
        headers = self.map_fields(fields, fields_map)

        # Order the object key/val by the order in display fields
        table_data = []

        # We're doing all of this just so we can pretty print dicts as k=v
        for obj in objects:
            obj_list = []
            for f in fields:
                field_data = obj[f]
                # If the field is a dict, pretty_dict it!
                if isinstance(field_data, dict):
                    field_data = self.pretty_dict(field_data)
                obj_list.append(field_data)
            table_data.append(obj_list)

        # table_data = [[obj[f] for f in fields] for obj in objects]
        table = tabulate.tabulate(table_data, headers=headers,
                                  tablefmt=tablefmt)

        # Only paginate if table is longer than terminal.
        t_height, _ = click.get_terminal_size()
        if len(table_data) > t_height:
            click.echo_via_pager(table)
        else:
            click.echo(table)

    def rebase(self, data):
        """If this is not a site object, then rebase the API URL."""
        site_id = data.pop('site_id', None)
        if site_id is not None:
            log.debug('Got site_id: %s; rebasing API URL!' % site_id)
            self.api._store['base_url'] += '/sites/' + site_id

    def add(self, data):
        """POST"""
        action = 'add'
        log.debug('adding %s' % data)
        self.rebase(data)

        try:
            result = self.resource.post(data)
        except HttpClientError as err:
            self.handle_error(action, data, err)
        else:
            self.handle_response(action, data, result)

    def list(self, data, display_fields=None):
        """GET"""
        action = 'list'
        log.debug('listing %s' % data)
        obj_id = data.get('id')  # If obj_id, it's a single object
        self.rebase(data)

        try:
            # Try getting a single object first
            if obj_id:
                result = self.resource(obj_id).get()
            # Or get all of them.
            else:
                result = self.resource.get(**data)
        except HttpClientError as err:
            self.handle_error(action, data, err)
        else:
            objects = []
            # Turn a single object into a list
            if obj_id:
                obj = result['data'][self.singular]
                objects = [obj]
            # Or just list all of them.
            elif result:
                objects = result['data'][self.resource_name]

            if objects:
                self.print_list(objects, display_fields)
            else:
                pretty_dict = self.pretty_dict(data)
                t_ = 'No %s found matching args: %s!'
                msg = t_ % (self.singular, pretty_dict)
                click.echo(msg)

    def remove(self, **data):
        """DELETE"""
        action = 'remove'
        obj_id = data['id']
        log.debug('removing %s' % obj_id)
        self.rebase(data)

        try:
            result = self.resource(obj_id).delete()
        except HttpClientError as err:
            self.handle_error(action, data, err)
        else:
            self.handle_response(action, data, result)

    def update(self, data):
        """PUT"""
        action = 'update'
        obj_id = data.pop('id')
        log.debug('updating %s' % data)
        self.rebase(data)

        # Get the original object by id first so that we can keep any existing
        # values without resetting them.
        try:
            obj = self.resource(obj_id).get()
        except HttpClientError as err:
            self.handle_error(action, data, err)
        else:
            model = ApiModel(obj)
            payload = dict(model)
            payload.pop('id')  # We don't want id when doing a PUT

        # Update the payload from the CLI params if the value isn't null.
        for k, v in data.iteritems():
            if v is not None:
                payload[k] = v

        # And now we call PUT
        try:
            result = self.resource(obj_id).put(payload)
        except HttpClientError as err:
            self.handle_error(action, data, err)
        else:
            self.handle_response(action, data, result)


@click.command(cls=NsotCLI, context_settings=CONTEXT_SETTINGS)
@click.option('-v', '--verbose', is_flag=True, help='Toggle verbosity.')
@click.version_option(version=pynsot.__version__)
@click.pass_context
def app(ctx, verbose):
    """NSoT command-line utility."""
    # This is the "app" object attached to all contexts.

    # Read the dotfile
    try:
        client_args = dotfile.Dotfile().read()
    except dotfile.DotfileError as err:
        raise click.UsageError(err.message)

    # Construct the App!
    ctx.obj = App(client_args=client_args, ctx=ctx, verbose=verbose)


if __name__ == '__main__':
    app()
