# -*- coding: utf-8 -*-

"""
Sub-command for Circuits
"""

from __future__ import absolute_import, unicode_literals
import logging

from pynsot.util import slugify
from pynsot.vendor import click
from . import callbacks
from .cmd_networks import DISPLAY_FIELDS as NETWORK_DISPLAY_FIELDS
from .cmd_interfaces import DISPLAY_FIELDS as INTERFACE_DISPLAY_FIELDS
from .cmd_devices import DISPLAY_FIELDS as DEVICE_DISPLAY_FIELDS


# Logger
log = logging.getLogger(__name__)

# Ordered list of 2-tuples of (field, display_name) used to translate object
# field names oto their human-readable form when calling .print_list().
DISPLAY_FIELDS = (
    ('id', 'ID'),
    ('name', 'Name'),
    ('endpoint_a', 'Endpoint A'),
    ('endpoint_z', 'Endpoint Z'),
    ('attributes', 'Attributes'),
)

# Fields to display when viewing a single record.
VERBOSE_FIELDS = DISPLAY_FIELDS


# Main group
@click.group()
@click.pass_context
def cli(ctx):
    """
    Circuit objects.

    A Circuit resource represents a connection between two interfaces on a
    device.
    """


# Add
# TODO(npegg): support specifying interfaces using the natural key instead of
# by ID when the API supports that
@cli.command()
@click.option(
    '-a',
    '--attributes',
    metavar='ATTRS',
    help='A key/value pair attached to this Circuit (format: key=value).',
    multiple=True,
    callback=callbacks.transform_attributes,
)
@click.option(
    '-A',
    '--endpoint-a',
    metavar='INTERFACE_ID',
    required=True,
    type=int,
    help='Unique ID of the interface of the A side of the Circuit',
)
@click.option(
    '-n',
    '--name',
    metavar='NAME',
    type=str,
    help='The name of the Circuit.',
)
@click.option(
    '-s',
    '--site-id',
    metavar='SITE_ID',
    type=int,
    help='Unique ID of the Site this Circuit is under. [required]',
    callback=callbacks.process_site_id,
)
@click.option(
    '-Z',
    '--endpoint-z',
    metavar='INTERFACE_ID',
    type=int,
    help='Unique ID of the interface on the Z side of the Circuit',
)
@click.pass_context
def add(ctx, attributes, endpoint_a, name, site_id, endpoint_z):
    """
    Add a new Circuit.

    You must provide the A side of the circuit using the -A/--endpoint-a
    option. The Z side is recommended but may be left blank, such as in cases
    where it is not an Interface that is tracked by NSoT (like a provider's
    interface).

    The name (-n/--name) is optional. If it is not specified, it will be
    generated for you in the form of:
    {device_a}:{interface_a}_{device_z}:{interface_z}

    If you wish to add attributes, you may specify the -a/--attributes
    option once for each key/value pair.
    """

    data = ctx.params

    # Remove empty values to facilitate default assignment
    if name is None:
        data.pop('name')
    if endpoint_z is None:
        data.pop('endpoint_z')

    ctx.obj.add(data)


# List
@cli.group(invoke_without_command=True)
@click.option(
    '-a',
    '--attributes',
    metavar='ATTRS',
    help='Filter Circuits by matching attributes (format: key=value).',
    multiple=True,
)
@click.option(
    '-A',
    '--endpoint-a',
    metavar='INTERFACE_ID',
    help='Filter to Circuits with endpoint_a interfaces that match this ID'
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
    help='Unique ID of the Circuit being retrieved.',
)
@click.option(
    '-l',
    '--limit',
    metavar='LIMIT',
    help='Limit result to N resources.',
)
@click.option(
    '-n',
    '--name',
    metavar='NAME',
    help='Filter to Circuits matching this name.',
)
@click.option(
    '-N',
    '--natural-key',
    is_flag=True,
    help='Display list results by their natural key',
    default=False,
    show_default=True,
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
    help='Perform a set query using Attributes and output matching Circuits.'
)
@click.option(
    '-s',
    '--site-id',
    metavar='SITE_ID',
    help='Unique ID of the Site this Circuit is under.',
    callback=callbacks.process_site_id,
)
@click.option(
    '-Z',
    '--endpoint-z',
    metavar='INTERFACE_ID',
    help='Filter to Circuits with endpoint_z interfaces that match this ID'
)
@click.pass_context
def list(ctx, attributes, endpoint_a, endpoint_z, grep, id, limit, name,
         natural_key, offset, query, site_id):
    """
    List existing Circuits for a Site.

    You must either have a Site ID configured in your .pysnotrc file or specify
    one using the -s/--site-id option.

    When listing Circuits, all objects are displayed by default. You optionally
    may look up a single Circuit by ID or Name using the -i/--id option.

    You may limit the number of results using the -l/--limit option.
    """

    # If we get a name as an identifier, slugify it
    if ctx.params.get('id') and not ctx.params['id'].isdigit():
        ctx.params['id'] = slugify(ctx.params['id'])

    # Don't list interfaces if a subcommand is invoked
    if ctx.invoked_subcommand is None:
        ctx.obj.list(ctx.params, display_fields=DISPLAY_FIELDS)


@list.command()
@click.pass_context
def addresses(ctx, *args, **kwargs):
    """ Show addresses for the Interfaces on this Circuit. """

    callbacks.list_subcommand(
        ctx, display_fields=NETWORK_DISPLAY_FIELDS, my_name=ctx.info_name
    )


@list.command()
@click.pass_context
def devices(ctx, *args, **kwargs):
    """ Show Devices connected by this Circuit. """

    callbacks.list_subcommand(
        ctx, display_fields=DEVICE_DISPLAY_FIELDS, my_name=ctx.info_name
    )


@list.command()
@click.pass_context
def interfaces(ctx, *args, **kwargs):
    """ Show Interfaces connected by this Circuit. """

    callbacks.list_subcommand(
        ctx, display_fields=INTERFACE_DISPLAY_FIELDS, my_name=ctx.info_name
    )


# Update
@cli.command()
@click.option(
    '-a',
    '--attributes',
    metavar='ATTRS',
    help='A key/value pair attached to this Circuit (format: key=value).',
    multiple=True,
    callback=callbacks.transform_attributes,
)
@click.option(
    '-A',
    '--endpoint-a',
    metavar='INTERFACE_ID',
    type=int,
    help='Unique ID of the interface of the A side of the Circuit',
)
@click.option(
    '-i',
    '--id',
    metavar='ID',
    help='Unique ID of the Circuit being retrieved.',
    required=True,
)
@click.option(
    '-n',
    '--name',
    metavar='NAME',
    type=str,
    help='The name of the Circuit.',
)
@click.option(
    '-s',
    '--site-id',
    metavar='SITE_ID',
    type=int,
    help='Unique ID of the Site this Circuit is under. [required]',
    callback=callbacks.process_site_id,
)
@click.option(
    '-Z',
    '--endpoint-z',
    metavar='INTERFACE_ID',
    type=int,
    help='Unique ID of the interface on the Z side of the Circuit',
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
@click.pass_context
def update(ctx, attributes, endpoint_a, id, name, site_id, endpoint_z,
           attr_action):
    """
    Update a Circuit.

    You must either have a Site ID configured in your .pysnotrc file or specify
    one using the -s/--site-id option.

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

    # If we get a name as an identifier, slugify it
    if ctx.params.get('id') and not ctx.params['id'].isdigit():
        ctx.params['id'] = slugify(ctx.params['id'])

    if not any([attributes, endpoint_a, name, endpoint_z]):
        msg = 'You must supply at least one of the optional arguments.'
        raise click.UsageError(msg)

    ctx.obj.update(ctx.params)


# Remove
@cli.command()
@click.option(
    '-i',
    '--id',
    metavar='ID',
    help='Unique ID of the Circuit being deleted.',
    required=True,
)
@click.option(
    '-s',
    '--site-id',
    metavar='SITE_ID',
    type=int,
    help='Unique ID of the Site this Circuit is under.',
    callback=callbacks.process_site_id,
)
@click.pass_context
def remove(ctx, id, site_id):
    """
    Remove a Circuit.

    You must either have a Site ID configured in your .pysnotrc file or specify
    one using the -s/--site-id option.

    When removing Circuits, all objects are displayed by default. You
    optionally may look up a single Circuit by ID or Name using the -i/--id
    option.
    """

    # If we get a name as an identifier, slugify it
    if ctx.params.get('id') and not ctx.params['id'].isdigit():
        ctx.params['id'] = slugify(ctx.params['id'])

    ctx.obj.remove(**ctx.params)
