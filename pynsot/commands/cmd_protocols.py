# -*- coding: utf-8 -*-

"""
Sub-command for Protocols.

In all cases ``data = ctx.params`` when calling the appropriate action method
on ``ctx.obj``. (e.g. ``ctx.obj.add(ctx.params)``)

Also, ``action = ctx.info_name`` *might* reliably contain the name of the
action function, but still not sure about that. If so, every function could be
fundamentally simplified to this::

    getattr(ctx.obj, ctx.info_name)(ctx.params)
"""

from __future__ import unicode_literals
import logging

from ..vendor import click
from . import callbacks, types


# Logger
log = logging.getLogger(__name__)

# Ordered list of 2-tuples of (field, display_name) used to translate object
# field names oto their human-readable form when calling .print_list().
DISPLAY_FIELDS = (
    ('id', 'ID'),
    ('device', 'Device'),
    ('type', 'Type'),
    ('interface', 'Interface'),
    ('circuit', 'Circuit'),
    ('attributes', 'Attributes'),
)

# Fields to display when viewing a single record.
VERBOSE_FIELDS = (
    ('id', 'ID'),
    ('device', 'Device'),
    ('type', 'Type'),
    ('interface', 'Interface'),
    ('circuit', 'Circuit'),
    ('auth_string', 'Auth_String'),
    ('description', 'Description'),
    ('site', 'Site'),
    ('attributes', 'Attributes'),
)


# Main group
@click.group()
@click.pass_context
def cli(ctx):
    """
    Protocol objects.

    A Protocol resource can represent a network routing protocol.

    """


# Add
@cli.command()
@click.option(
    '-u',
    '--auth_string',
    metavar='AUTH_STRING',
    default='',
    help='The authentication string (such as MD5 sum).',
)
@click.option(
    '-a',
    '--attributes',
    metavar='ATTRS',
    help='A key/value pair attached to this Protocol (format: key=value).',
    multiple=True,
    callback=callbacks.transform_attributes,
)
@click.option(
    '-c',
    '--circuit',
    metavar='CIRCUIT',
    help='The circuit that this protocol is running over.',
)
@click.option(
    '-D',
    '--device',
    metavar='DEVICE',
    type=types.NATURAL_KEY,
    help=(
        'Unique ID of the Device to which this Protocol is '
        'running on.'
    ),
    required=True,
)
@click.option(
    '-e',
    '--description',
    metavar='DESCRIPTION',
    type=str,
    help='The description for this Protocol.',
)
@click.option(
    '-I',
    '--interface',
    metavar='INTERFACE',
    type=str,
    help=(
        'The Interface this Protocol is running on. Either interface'
        'or circuit must be populated.'
    ),
)
@click.option(
    '-s',
    '--site-id',
    metavar='SITE_ID',
    type=int,
    help=(
        'Unique ID of the Site this Protocol is under.'
        'If not set, this will be inherited off of the device\'s site'
    ),
    callback=callbacks.process_site_id,
)
@click.option(
    '-t',
    '--type',
    metavar='TYPE',
    type=types.NATURAL_KEY,
    help='The type of the protocol.',
    required=True,
)
@click.pass_context
def add(ctx, auth_string, attributes, circuit, device, description, interface,
        site_id, type):
    """
    Add a new Protocol.

    You must provide a Device hostname or ID using the -D/--device option.

    You must provide the type of the protocol (e.g. OSPF, BGP, etc.)

    If you wish to add attributes, you may specify the -a/--attributes
    option once for each key/value pair.

    """
    data = ctx.params

    if interface is None and circuit is None:
        raise click.UsageError(
            '''Must have interface "-i" / "--interface" or
               circuit "-c" / "--circuit" populated'''
        )

    if description is None:
        data.pop('description')

    ctx.obj.add(data)


# List
@cli.group(invoke_without_command=True)
@click.option(
    '-a',
    '--attributes',
    metavar='ATTRS',
    help='A key/value pair attached to this Protocol (format: key=value).',
    multiple=True,
)
@click.option(
    '-u',
    '--auth_string',
    metavar='AUTH_STRING',
    default='',
    help='The authentication string (such as MD5 sum).',
)
@click.option(
    '-c',
    '--circuit',
    metavar='CIRCUIT',
    help='The circuit that this protocol is running over.',
)
@click.option(
    '-d',
    '--delimited',
    is_flag=True,
    help='Display set query results separated by commas vs. newlines.',
    default=False,
    show_default=True,
)
@click.option(
    '-e',
    '--description',
    metavar='DESCRIPTION',
    type=str,
    help='Filter by Protocols matching this description.',
)
@click.option(
    '-D',
    '--device',
    metavar='DEVICE',
    type=types.NATURAL_KEY,
    help=(
        'Unique ID of the Device to which this Protocol is '
        'running on.'
    ),
)
@click.option(
    '-g',
    '--grep',
    is_flag=True,
    help='Display list results in a grep-friendly format.',
    default=False,
    show_default=True,
)
@click.option(
    '-i',
    '--id',
    metavar='ID',
    help='Unique ID of the Protocol being retrieved.',
)
@click.option(
    '-I',
    '--interface',
    metavar='INTERFACE',
    type=types.NATURAL_KEY,
    help=(
        'The Interface this Protocol is running on. Either interface'
        'or circuit must be populated.'
    ),
)
@click.option(
    '-l',
    '--limit',
    metavar='LIMIT',
    type=int,
    help='Limit result to N resources.',
)
@click.option(
    '-o',
    '--offset',
    metavar='OFFSET',
    help='Skip the first N resources.',
)
@click.option(
    '-q',
    '--query',
    metavar='QUERY',
    help='Perform a set query using Attributes and output matching Protocols.'
)
@click.option(
    '-s',
    '--site-id',
    metavar='SITE_ID',
    help='Unique ID of the Site this Protocol is under.',
    callback=callbacks.process_site_id,
)
@click.option(
    '-t',
    '--type',
    metavar='TYPE',
    type=types.NATURAL_KEY,
    help='The protocol type',
)
@click.pass_context
def list(ctx, attributes, auth_string, circuit, delimited, description, device,
         grep, id, interface, limit, offset, query, site_id, type):
    """
    List existing Protocols for a Site.

    You must provide a Site ID using the -s/--site-id option.

    You must provide the protocol type.

    When listing Protocols, all objects are displayed by default. You
    optionally may lookup a single Protocols by ID using the -i/--id option.

    You may look up the protocols for a single Device using -D/--device which
    can be either a hostname or ID for a Device.
    """
    data = ctx.params
    data.pop('delimited')  # We don't want this going to the server.

    # If we provide ID, show more fields
    if id is not None:
        display_fields = VERBOSE_FIELDS
    else:
        display_fields = DISPLAY_FIELDS

    # If we aren't passing a sub-command, just call list(), otherwise let it
    # fallback to default behavior.
    if ctx.invoked_subcommand is None:
        if query is not None:
            ctx.obj.natural_keys_by_query(data, delimited)
        else:
            ctx.obj.list(
                data, display_fields=display_fields,
                verbose_fields=VERBOSE_FIELDS
            )


# Remove
@cli.command()
@click.option(
    '-i',
    '--id',
    metavar='ID',
    help='Unique ID of the Protocol being deleted.',
    required=True,
)
@click.option(
    '-s',
    '--site-id',
    metavar='SITE_ID',
    type=int,
    help='Unique ID of the Site this Protocol is under.',
    callback=callbacks.process_site_id,
    required=True,
)
@click.pass_context
def remove(ctx, id, site_id):
    """
    Remove a Protocol.

    You must provide a Site ID using the -s/--site-id option.

    When removing an Protocol, you must provide the ID of the Protocol using
    -i/--id.

    You may retrieve the ID for an Protocol by parsing it from the list of
    Protocols for a given Site:

        nsot interfaces list --site-id <site_id> | grep <protocol>
    """
    data = ctx.params
    ctx.obj.remove(**data)


# Update
@cli.command()
@click.option(
    '-a',
    '--attributes',
    metavar='ATTRS',
    help='A key/value pair attached to this Protocol (format: key=value).',
    multiple=True,
    callback=callbacks.transform_attributes,
)
@click.option(
    '-u',
    '--auth_string',
    metavar='AUTH_STRING',
    default='',
    help='The authentication string (such as MD5 sum).',
)
@click.option(
    '-c',
    '--circuit',
    metavar='CIRCUIT',
    help='The circuit that this protocol is running over.',
)
@click.option(
    '-e',
    '--description',
    metavar='DESCRIPTION',
    type=str,
    help='The description for this Protocol.',
)
@click.option(
    '-D',
    '--device',
    metavar='DEVICE',
    type=types.NATURAL_KEY,
    help=(
        'Unique ID of the Device to which this Protocol is '
        'running on.'
    ),
)
@click.option(
    '-i',
    '--id',
    metavar='ID',
    type=int,
    help='Unique ID or natural key of the Protocol being updated.',
    required=True,
)
@click.option(
    '-I',
    '--interface',
    metavar='INTERFACE',
    type=types.NATURAL_KEY,
    help=(
        'The Interface this Protocol is running on. Either interface'
        'or circuit must be populated.'
    ),
)
@click.option(
    '-s',
    '--site-id',
    metavar='SITE_ID',
    type=int,
    help='Unique ID of the Site this Protocol is under.',
    callback=callbacks.process_site_id,
)
@click.option(
    '-t',
    '--type',
    metavar='TYPE',
    type=types.NATURAL_KEY,
    help='The Protocol type ID.',
)
@click.option(
    '--add-attributes',
    'attr_action',
    flag_value='add',
    default=True,
    help=(
        'Causes attributes to be added. This is the default and providing it '
        'will have no effect.'
    )
)
@click.option(
    '--delete-attributes',
    'attr_action',
    flag_value='delete',
    help=(
        'Causes attributes to be deleted instead of updated. If combined with'
        'with --multi the attribute will be deleted if either no value is '
        'provided, or if attribute no longer has an valid values.'
    ),
)
@click.option(
    '--replace-attributes',
    'attr_action',
    flag_value='replace',
    help=(
        'Causes attributes to be replaced instead of updated. If combined '
        'with --multi, the entire list will be replaced.'
    ),
)
@click.option(
    '--multi',
    is_flag=True,
    help='Treat the specified attributes as a list type.',
)
@click.pass_context
def update(ctx, attributes, auth_string, circuit, description, device, id,
           interface, site_id, type, attr_action, multi):
    """
    Update a Protocol.

    You must provide a Site ID using the -s/--site-id option.

    You must provide the type of the protocol (e.g. OSPF, BGP, etc.)

    When updating an Protocol you must provide the ID (-i/--id) and at least
    one of the optional arguments.

    The -a/--attributes option may be provided multiple times, once for each
    key-value pair.

    When modifying attributes you have three actions to choose from:

    * Add (--add-attributes). This is the default behavior that will add
    attributes if they don't exist, or update them if they do.

    * Delete (--delete-attributes). This will cause attributes to be
    deleted. If combined with --multi the attribute will be deleted if
    either no value is provided, or if the attribute no longer contains a
    valid value.

    * Replace (--replace-attributes). This will cause attributes to
    replaced. If combined with --multi and multiple attributes of the same
    name are provided, only the last value provided will be used.
    """
    if not any([attributes, description, type, auth_string, circuit,
                interface]):
        msg = 'You must supply at least one of the optional arguments.'
        raise click.UsageError(msg)
    ctx.obj.update(ctx.params)
