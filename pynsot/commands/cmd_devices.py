# -*- coding: utf-8 -*-

"""
Sub-command for Devices.

In all cases ``data = ctx.params`` when calling the appropriate action method
on ``ctx.obj``. (e.g. ``ctx.obj.add(ctx.params)``)

Also, ``action = ctx.info_name`` *might* reliably contain the name of the
action function, but still not sure about that. If so, every function could be
fundamentally simplified to this::

    getattr(ctx.obj, ctx.info_name)(ctx.params)
"""

from __future__ import unicode_literals

from ..vendor import click
from . import callbacks


# Ordered list of 2-tuples of (field, display_name) used to translate object
# field names oto their human-readable form when calling .print_list().
DISPLAY_FIELDS = (
    ('id', 'ID'),
    ('hostname', 'Hostname'),
    # ('site_id': 'Site ID'),
    ('attributes', 'Attributes'),
)


# Main group
@click.group()
@click.pass_context
def cli(ctx):
    """
    Device objects.

    A device represents various hardware components on your network such as
    routers, switches, console servers, PDUs, servers, etc.

    Devices also support arbitrary attributes similar to Networks.
    """


# Add
@cli.command()
@click.option(
    '-a',
    '--attributes',
    metavar='ATTRS',
    help='A key/value pair attached to this Device (format: key=value).',
    multiple=True,
    callback=callbacks.transform_attributes,
)
@click.option(
    '-b',
    '--bulk-add',
    metavar='FILENAME',
    help='Bulk add Devices from the specified colon-delimited file.',
    type=click.File('rb'),
    callback=callbacks.process_bulk_add,
)
@click.option(
    '-H',
    '--hostname',
    metavar='HOSTNAME',
    help='The hostname of the Device.  [required]',
)
@click.option(
    '-s',
    '--site-id',
    metavar='SITE_ID',
    type=int,
    help='Unique ID of the Site this Device is under.  [required]',
    callback=callbacks.process_site_id,
)
@click.pass_context
def add(ctx, attributes, bulk_add, hostname, site_id):
    """
    Add a new Device.

    You must provide a Site ID using the -s/--site-id option.

    When adding a new Device, you must provide a value for the -H/--hostname
    option.

    If you wish to add attributes, you may specify the -a/--attributes
    option once for each key/value pair.
    """
    data = bulk_add or ctx.params

    # Enforce required options
    if bulk_add is None:
        if hostname is None:
            raise click.UsageError('Missing option "-H" / "--hostname".')

    ctx.obj.add(data)


# List
# @cli.command()
@cli.group(invoke_without_command=True)
@click.option(
    '-a',
    '--attributes',
    metavar='ATTRS',
    help='Filter Devices by matching attributes (format: key=value).',
    multiple=True,
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
    '-g',
    '--grep',
    is_flag=True,
    help='Display list results in a grep-friendly format.',
    default=False,
    show_default=True,
)
@click.option(
    '-H',
    '--hostname',
    metavar='HOSTNAME',
    help='Filter by hostname of the Device.',
)
@click.option(
    '-i',
    '--id',
    metavar='ID',
    type=int,
    help='Unique ID of the Device being retrieved.',
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
    help='Perform a set query using Attributes and output matching hostnames.',
)
@click.option(
    '-s',
    '--site-id',
    metavar='SITE_ID',
    type=int,
    help='Unique ID of the Site this Device is under.  [required]',
    callback=callbacks.process_site_id,
)
@click.pass_context
def list(ctx, attributes, delimited, grep, hostname, id, limit, natural_key,
         offset, query, site_id):
    """
    List existing Devices for a Site.

    You must provide a Site ID using the -s/--site-id option.

    When listing Devices, all objects are displayed by default. You may
    optionally lookup a single Device by ID using the -i/--id option.

    You may limit the number of results using the -l/--limit option.
    """
    data = ctx.params
    data.pop('delimited')  # We don't want this going to the server.

    if ctx.invoked_subcommand is None:
        if query is not None:
            ctx.obj.set_query(data, delimited)
        else:
            ctx.obj.list(data, display_fields=DISPLAY_FIELDS)


@list.command()
@click.pass_context
def interfaces(ctx, *args, **kwargs):
    """Get interfaces for a Device."""
    from .cmd_interfaces import DISPLAY_FIELDS as INTERFACE_DISPLAY_FIELDS
    callbacks.list_subcommand(
        ctx, display_fields=INTERFACE_DISPLAY_FIELDS, my_name='interfaces'
    )


# Remove
@cli.command()
@click.option(
    '-H',
    '--hostname',
    'id',
    metavar='HOSTNAME',
    type=str,
    help='The hostname of the Device being deleted.',
)
@click.option(
    '-i',
    '--id',
    metavar='ID',
    help='Unique ID of the Device being deleted.',
    required=True,
)
@click.option(
    '-s',
    '--site-id',
    metavar='SITE_ID',
    type=int,
    help='Unique ID of the Site this Device is under.  [required]',
    callback=callbacks.process_site_id,
)
@click.pass_context
def remove(ctx, id, site_id):
    """
    Remove a Device.

    You must provide a Site ID using the -s/--site-id option.

    When removing a Device, you must either provide the unique ID using
    -i/--id, or the hostname of the Device using -H/--hostname.

    If both are provided, -H/--hostname will be ignored.
    """
    data = ctx.params
    ctx.obj.remove(**data)


# Update
@cli.command()
@click.option(
    '-a',
    '--attributes',
    metavar='ATTRS',
    help='A key/value pair attached to this network (format: key=value).',
    multiple=True,
    callback=callbacks.transform_attributes,
)
@click.option(
    '-H',
    '--hostname',
    metavar='HOSTNAME',
    help='The hostname of the Device.',
)
@click.option(
    '-i',
    '--id',
    metavar='ID',
    type=int,
    help='Unique ID of the Device being updated.',
)
@click.option(
    '-s',
    '--site-id',
    metavar='SITE_ID',
    type=int,
    help='Unique ID of the Site this Device is under.  [required]',
    callback=callbacks.process_site_id,
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
        ' with --multi, the entire list will be replaced.'
    ),
)
@click.option(
    '--multi',
    is_flag=True,
    help='Treat the specified attributes as a list type.',
)
@click.pass_context
def update(ctx, attributes, hostname, id, site_id, attr_action, multi):
    """
    Update a Device.

    You must provide a Site ID using the -s/--site-id option.

    When updating a Device you must provide either the unique ID (-i/--id) or
    hostname (-H/--hostname) and at least one of the optional arguments. If
    -i/--id is provided -H/--hostname will be ignored.

    If you desire to update the hostname field, you must provide -i/--id to
    uniquely identify the Device.

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
    if not any([attributes, hostname]):
        msg = 'You must supply at least one of the optional arguments.'
        raise click.UsageError(msg)

    if not id and not hostname:
        raise click.UsageError(
            'You must provide -H/--hostname when not providing -i/--id.'
        )

    data = ctx.params
    ctx.obj.update(data)
