# -*- coding: utf-8 -*-

"""
Base CLI commands for all objects.

Model-specific objects and argument parsers will be defined in subclasses or by
way of factory methods.
"""

from __future__ import unicode_literals
import datetime
import logging
import os
import sys
import textwrap

import pynsot
from . import client
from .util import get_result

from .vendor import click, netaddr, prettytable
from .vendor.slumber.exceptions import (HttpClientError, HttpServerError)


# Constants/Globals
if os.getenv('PYNSOT_DEBUG'):
    logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

# Make the --help option also have -h
CONTEXT_SETTINGS = {
    'help_option_names': ['-h', '--help'],
}

# Tuple of HTTP errors used for exception handling
HTTP_ERRORS = (HttpClientError, HttpServerError)

# Where to find the command plugins.
CMD_FOLDER = os.path.abspath(
    os.path.join(os.path.dirname(__file__), 'commands')
)


# Mapping of resource_names to natural_keys. This is primarily used by
# App.get_single_object() to map parameters to a single object.
NATURAL_KEYS = {
    'devices': ['hostname'],
    'networks': ['cidr'],
    'attributes': ['name', 'resource_name'],
    'interfaces': ['name', 'device'],
}

# Mapping of resource_names to what we want objects to look like when formatted
# to stdout for grep-friendliness. These are string interpolation style.
GREP_FORMATS = {
    'devices': '%(hostname)s',
    'networks': '%(network_address)s/%(prefix_length)s',
    'addresses': '%(network_address)s/%(prefix_length)s',  # Same as networks
    'assignments': '%(hostname)s:%(interface_name)s:%(address)s',
    'attributes': '%(resource_name)s:%(name)s',
    'circuits': '%(name)s',
    'interfaces': '%(device_hostname)s:%(name)s',
    'sites': '%(name)s',
}


__all__ = (
    'NsotCLI', 'App', 'app'
)


class NsotCLI(click.MultiCommand):
    """
    Base command object used to define object-specific command-line parsers.

    This will load command plugins from the "commands" folder.

    Plugins must be named "cmd_{foo}.py" and must have a top-level command
    named "cli".
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
        return mod.cli  # Each cmd_ plugin defines top-level "cli" command


class App(object):
    """Context object for holding state data for the CLI app."""
    def __init__(self, ctx, client_args=None, verbose=False):
        if client_args is None:
            client_args = {}

        # Force api_version 1.0 for CLI util.
        client_args['extra_args'] = {'api_version': '1.0'}

        self.client_args = client_args
        self.ctx = ctx
        self.verbose = verbose
        self.resource_name = self.ctx.invoked_subcommand
        self.grep_name = self.resource_name
        self.site_id = None  # This is populated later.
        self.rebase_done = False  # So that we only rebase once.

    @property
    def api(self):
        """This way the API client is not created until called."""
        if not hasattr(self, '_api'):
            self._api = client.get_api_client(**self.client_args)
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
    def pretty_dict(data, delim='=', sep=', ', joiner='\n'):
        """
        Return a dict in k=v format. And also make it nice to look at.

        :param dict:
            A dict

        :param sep:
            Character used to separate items

        :param joiner:
            Character used to join items
        """
        log.debug('PRETTY DICT INCOMING DATA = %r', data)
        pretty = ''
        for key, val in data.iteritems():
            if isinstance(val, list):
                # Sort, add a newline and indent so that nested value items
                # look better.
                val = joiner.join(' ' + i for i in sorted(val))
                if val:
                    val = joiner + val  # Prefix it w/ newline for readability
            pretty += '%s%s%s%s' % (key, delim, val, sep)

        return pretty.rstrip(sep)  # Drop the trailing separator

    def format_message(self, obj_single, message=''):
        """
        Attempt to make messages human-readable.

        :param obj_single:
            Singular object name

        :param message:
            Dat message tho!
        """
        log.debug('FORMATTING MESSAGE: %r' % (message,))
        if 'UNIQUE constraint failed' in message:
            message = '%s object already exists.' % (obj_single.title(),)
        return message

    def format_timestamp(self, ts):
        """
        Take a UNIX timestamp and make it a datetime string.

        :param ts:
            UNIX timestamp
        """
        ts = int(ts)
        dt = datetime.datetime.fromtimestamp(ts)
        return str(dt)

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
            log.debug('API ERROR: %r' % (body,))

            msg = body['error']['message']
            msg = self.format_message(obj_single, msg)

            # Add the status code and reason to the output
            log.debug('ERROR MESSAGE = %r' % (msg,))
            if self.verbose or not msg:
                t_ = '%s %s'
                reason = resp.reason.upper()
                extra += t_ % (resp.status_code, reason)
            if not msg:
                msg = extra.strip()
        else:
            msg = str(err)

        if isinstance(msg, dict):
            msg = self.pretty_dict(msg, delim=': ', joiner='')

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
        if isinstance(data, list):
            for item in data:
                self.handle_response(action, item, result)
            return None

        t_ = '%s %s!'
        if action.endswith('e'):
            action = action[:-1]  # "remove" -> "remov"
        action = action.title() + 'ed'  # "remove" -> "removed"
        msg = t_ % (action, self.singular)

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
        log.debug('MAP_FIELDS HEADERS = %r' % (headers,))
        return headers

    def format_field(self, field, field_data):
        """
        Specially format a field.

        :param field:
            Field name

        :param field_data:
            Field data dict
        """
        # If it's a user field, only show the email
        if field == 'user':
            field_data = field_data['email']

        # Arbitrarily wrap description field at 20 chars
        if field == 'description':
            field_data = '\n'.join(textwrap.wrap(field_data, 20))

        # If the field is a dict, pretty_dict it!
        if isinstance(field_data, dict):
            # If this is an inner dict, prettify it, too.
            for sub_field in ('attributes', 'constraints'):
                if sub_field in field_data:
                    field_data[sub_field] = self.pretty_dict(
                        field_data[sub_field], sep='\n')

            # This is so that k=v looks better when printing a resource's
            # contents
            if field == 'resource':
                delim = ':'
            # Otherwise we just fallback to standard k=v
            else:
                delim = '='
            field_data = self.pretty_dict(field_data, delim=delim, sep='\n')

        if isinstance(field_data, list):
            field_data = '\n'.join(field_data)

        # If it's the 'change_at' field, make it human-readable
        elif field == 'change_at':  # Timestamp
            field_data = self.format_timestamp(field_data)

        return field_data

    def format_object_for_grep(self, obj):
        """
        Formats an object... for grep.

        :param obj:
            Object
        """
        # If there's a "grep_name", use that, otherwise use resource_name
        grep_name = getattr(self, 'grep_name', self.resource_name)

        return GREP_FORMATS[grep_name] % obj

    def print_grep(self, objects):
        """
        Print a list of objects in a grep-friendly format.

        Attributes are displayed in key=value style, one per line.

        :param objects:
            List of objects
        """
        output = []
        for obj in objects:
            prefix = self.format_object_for_grep(obj)
            attrs = obj.get('attributes', {})
            keys = sorted(attrs)
            for k in keys:
                output.append('%s %s=%s' % (prefix, k, attrs[k]))

        click.echo('\n'.join(output))

    def print_by_natural_key(self, objects, delimiter='\n'):
        """
        Print a list of objects by their natural_key

        :param objects:
            List of objects

        :param delimiter:
            Character used to delimit objects
        """
        output = []
        for obj in objects:
            output.append(self.format_object_for_grep(obj))

        # Networks results must be specially sorted.
        if self.grep_name != 'networks':
            output = sorted(output)
        else:
            networks = sorted(
                netaddr.IPNetwork(d) for d in output
            )
            output = (str(n) for n in networks)

        click.echo(delimiter.join(output))

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
        headers = self.map_fields(fields, fields_map)

        # Order the object key/val by the order in display fields
        table_data = []

        # We're doing all of this just so we can pretty print dicts as k=v
        for obj in objects:
            obj_list = []
            for field in fields:
                field_data = obj[field]

                # Attempt to format the field
                field_data = self.format_field(field, field_data)

                obj_list.append(field_data)
            table_data.append(obj_list)

        # Prepare the table object
        table = prettytable.PrettyTable(headers)

        # Display table in a frame
        table.vrules = prettytable.prettytable.FRAME

        # *or* Display table with row separators
        # table.hrules = prettytable.ALL
        # table.vrules = prettytable.NONE

        table.align = 'l'  # Left-align everything
        table.left_padding_width = 1

        # Add the table rows
        for row in table_data:
            table.add_row(row)

        # Only paginate if table is longer than terminal.
        _, t_height, = click.get_terminal_size()
        if len(table_data) > t_height:
            click.echo_via_pager(table)
        else:
            click.echo(table)

    def rebase(self, data):
        """
        If this is not a Site object, then rebase the API URL.

        :param data:
            Dict of query arguments
        """
        # Don't rebase again if we've already rebased.
        if self.rebase_done:
            return None

        # Handle bulk queries
        if isinstance(data, list):
            data = data[0]

        # Prefer site_id from args.
        site_id = data.pop('site_id', None)

        # Default to client's default_site provided in user's config or at CLI.
        if site_id is None and self.resource_name != 'sites':
            site_id = self.api.default_site

        log.debug('rebase: Got site_id: %s' % site_id)
        if site_id is not None:
            log.debug('rebase: Site_id found; rebasing API URL!')
            self.site_id = site_id
            self.api._store['base_url'] += '/sites/%s' % site_id

        # Mark rebase as done.
        self.rebase_done = True

    def add(self, data):
        """POST"""
        action = 'add'
        log.debug('adding %s' % data)
        self.rebase(data)

        try:
            result = self.resource.post(data)
        except HTTP_ERRORS as err:
            self.handle_error(action, data, err)
        else:
            self.handle_response(action, data, result)

    def get_single_object(self, data, resource=None, natural_keys=None):
        """
        Get a single object based on the natural key for this resource.

        :param data:
            Dict of query parameters

        :param resource:
            (Optional) API resource object

        :param natural_keys:
            (Optional) List of natural keys. If not provided, they are derived
            automatically from the resource.

        :returns:
            None
        """
        # Should be a list of natural keys for the resource
        if natural_keys is None:
            natural_keys = NATURAL_KEYS.get(self.resource_name, [])

        # Construct our params to retrieve a single object.
        params = {'limit': 1}
        for natural_key in natural_keys:
            natural_value = data.get(natural_key)

            # Only filter if the key was found. This is mostly for interfaces
            # where (device_id,) or (device_id, name) are valid lookups.
            if natural_value is not None:
                params[natural_key] = natural_value

        # Rebase before we toilet face.
        if resource is None:
            resource = self.resource

        # Get the results
        try:
            r = resource.get(**params)
        except HTTP_ERRORS:
            return None

        # Assert only 1 matching result.
        try:
            total = r['count']
        except KeyError:
            return r  # Single result such as from /api/networks/:id/parent/

        if total > 1:
            log.debug('get_single_object: More than one object found!')
            return None

        # Return a single result.
        r = get_result(r)
        try:
            return r[0]
        except IndexError:
            return None

    def detail(self, data, resource):
        """
        GET a detail endpoint and return the results.

        This method is currently only called for Network.next_address() and
        Network.next_network(), so its use-case is very specific.

        :param data:
            Dict of query parameters

        :param resource:
            A prepared API resource object
        """
        try:
            return resource.get(**data)
        except HTTP_ERRORS as err:
            self.handle_error('detail', data, err)

    def set_query(self, data, delimited=False):
        """
        Run a set query and return the results.

        :param data:
            Dict of query parameters

        :param delimited:
            Whether to display the results as comma or newline delimited
        """
        self.rebase(data)
        try:
            results = self.resource.query.get(**data)
        except HTTP_ERRORS as err:
            self.handle_error('list', data, err)

        objects = get_result(results)
        delimiter = ',' if delimited else '\n'
        self.print_by_natural_key(objects, delimiter)

    def list(self, data, display_fields=None, resource=None,
             verbose_fields=None):
        """
        GET objects and display them to stdout.

        :param data:
            Dict of query parameters

        :param display_fields:
            Mapping of field_names to list display

        :param resource:
            (Optional) API resource object

        :param verbose_fields:
            (Optional) Mapping of field_names to verbose detail display. If not
            provided, ``display_fields`` is used.
        """
        action = 'list'
        log.debug('listing %s' % data)
        obj_id = data.get('id')  # If obj_id, it's a single object

        grep = data.pop('grep', False)
        by_natural_key = data.pop('natural_key', False)

        # If a resource object is provided, call it instead, and only rebase if
        # we haven't provided our own resource.
        if resource is None:
            self.rebase(data)  # Rebase first
            resource = self.resource

        obj = None
        try:
            # Try getting a single object first
            if obj_id:
                log.debug('Retrieving by obj_id=%r' % obj_id)
                result = resource(obj_id).get()
                obj = get_result(result)

            # If we still don't have an object try param-based lookup.
            if obj is None:
                log.debug('Retrieving by single_object')
                obj = self.get_single_object(data, resource)

            # If obj is STILL None...
            if obj is not None:
                # Set display_fields to verbose
                display_fields = verbose_fields or display_fields
            else:
                log.debug('Retrieving by params=%r' % data)
                result = resource.get(**data)

        except HTTP_ERRORS as err:
            self.handle_error(action, data, err)

        else:
            objects = []

            # Turn a single object into a list
            if obj:
                objects = [obj]

            # Or just list all of them.
            elif result:
                objects = get_result(result)

            if objects:
                if grep:
                    self.print_grep(objects)
                elif by_natural_key:
                    self.print_by_natural_key(objects)
                else:
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
        except HTTP_ERRORS as err:
            self.handle_error(action, data, err)
        else:
            self.handle_response(action, data, result)

    def process_attributes(self, attrs, action, multi=False):
        """
        Return a merged dict of CLI attribute actions w/ existing attributes.

        Turn attribute/value pairs into actionable attributes that the API can
        consume.

        :param attrs:
            Dictionary of outgoing attributes to merge with

        :param action:
            The action to perform against the outgoing attributes

        :param multi:
            Whether to treat the incoming attributes as list types
        """
        log.debug('PROCESS_ATTRIBUTES [IN]: %r', attrs)

        log.debug('ATTRIBUTES = %r', self.ctx._attributes)
        log.debug('ATTR_ACTION = %r', action)
        log.debug('      MULTI = %r', multi)

        multi_replaced = False
        for key, val in self.ctx._attributes:
            # List-type handler
            if multi:
                if action == 'add':
                    log.debug('[multi] Adding %r to %r' % (val, key))
                    if key not in attrs:
                        attrs[key] = [val]
                    elif val not in attrs[key]:
                        attrs[key].append(val)
                elif action == 'replace':
                    log.debug('[multi] Replacing %r with [%r]' % (key, val))
                    if key in attrs and not multi_replaced:
                        attrs[key] = []
                        multi_replaced = True

                    if val not in attrs[key]:
                        attrs[key].append(val)
                elif action == 'delete':
                    log.debug('[multi] Removing %r from %r' % (val, key))
                    # Remove this item from the list
                    if val in attrs[key]:
                        attrs[key].remove(val)

                    # If the value wasn't provided, or if the list is now
                    # empty, remove it.
                    if not val or not attrs[key]:
                        attrs.pop(key)

            # Default string-based handler
            else:
                if action in ('add', 'replace'):
                    log.debug(
                        '[single] Adding/replacing %r to %r' % (val, key)
                    )
                    attrs[key] = val
                elif action == 'delete':
                    log.debug('[single] Removing %r from %r' % (val, key))
                    attrs.pop(key, None)

        log.debug('PROCESS_ATTRIBUTES [OUT]: %r', attrs)
        return attrs

    def update(self, data):
        """PUT"""

        action = 'update'
        obj_id = data.pop('id')
        attr_action = data.pop('attr_action', None)
        multi = data.get('multi', False)
        log.debug('updating %s' % data)
        self.rebase(data)

        # Get the original object by id first so that we can keep any existing
        # values without resetting them.
        try:
            if obj_id:
                log.debug('Retrieving by obj_id=%r' % obj_id)
                result = self.resource(obj_id).get()
                obj = get_result(result)
            else:
                obj = self.get_single_object(data)
        except HTTP_ERRORS as err:
            self.handle_error(action, data, err)
        else:
            # FIXME(jathan) This error case needs work. It needs to be as
            # descriptive as when a lookup by id fails.
            if obj is None:
                self.handle_error(
                    action, data,
                    'Update failed. Try again with --verbose for more info.'
                )

            obj_id = obj.pop('id')  # We don't want id when doing a PUT
            payload = obj

        log.debug('PAYLOAD [in]: %r', payload)

        # Update the payload from the CLI params if the value isn't null.
        for key, val in data.iteritems():
            # If we're updating attributes, reconcile with existing attributes
            if key == 'attributes':
                attrs = payload['attributes']
                payload['attributes'] = self.process_attributes(
                    attrs, attr_action, multi=multi
                )

            # Otherwise, if the value was provided, replace it outright
            elif val is not None:
                payload[key] = val

        log.debug('PAYLOAD [out]: %r', payload)
        # And now we call PUT
        try:
            result = self.resource(obj_id).put(payload)
            log.debug('RESULT [out]: %r', result)
        except HTTP_ERRORS as err:
            self.handle_error(action, data, err)
        else:
            self.handle_response(action, data, result)


@click.command(cls=NsotCLI, context_settings=CONTEXT_SETTINGS)
@click.option('-v', '--verbose', is_flag=True, help='Toggle verbosity.')
@click.version_option(version=pynsot.__version__)
@click.pass_context
def app(ctx, verbose):
    """
    Network Source of Truth (NSoT) command-line utility.

    For detailed documentation, please visit https://nsot.readthedocs.io
    """
    # This is the "app" object attached to all contexts.
    ctx.obj = App(ctx=ctx, verbose=verbose)

    # Store the invoked_subcommand (e.g. 'networks') name as
    # parent_resource_name so that descendent sub-commands can reference where
    # they came from, such as when calling callbacks.list_subcommand()
    ctx.obj.parent_resource_name = ctx.invoked_subcommand


if __name__ == '__main__':
    app()
