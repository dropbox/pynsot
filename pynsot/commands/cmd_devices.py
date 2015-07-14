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

__author__ = 'Jathan McCollum'
__maintainer__ = 'Jathan McCollum'
__email__ = 'jathan@dropbox.com'
__copyright__ = 'Copyright (c) 2015 Dropbox, Inc.'


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

    When adding a new Device, you must provide a value for the -h/--hostname
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
@cli.command()
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
def list(ctx, attributes, delimited, hostname, id, limit, offset, query, site_id):
    """
    List existing Devices for a Site.

    You must provide a Site ID using the -s/--site-id option.

    When listing Devices, all objects are displayed by default. You may
    optionally lookup a single Device by ID using the -i/--id option.

    You may limit the number of results using the -l/--limit option.
    """
    data = ctx.params
    data.pop('delimited')  # We don't want this going to the server.

    if query:
        results = ctx.obj.api.sites(site_id).devices.query.get(
            query=query, limit=limit, offset=offset)
        objects = results['data']['devices']
        devices = sorted(d['hostname'] for d in objects)
        joiner = ',' if delimited else '\n'
        click.echo(joiner.join(devices))
    else:
        ctx.obj.list(data, display_fields=DISPLAY_FIELDS)


# Remove
@cli.command()
@click.option(
    '-i',
    '--id',
    metavar='ID',
    type=int,
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

    When removing a Device, you must provide the unique ID using -i/--id. You
    may retrieve the ID for a Device by parsing it from the list of Devices
    for a given Site:

        nsot devices list --site-id <site_id> | grep <hostname>
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
@click.option(
    '-A',
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
    '-d',
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
    '-r',
    '--replace-attributes',
    'attr_action',
    flag_value='replace',
    help=(
        'Causes attributes to be replaced instead of updated. If combined with '
        '--multi, the entire list will be replaced.'
    ),
)
@click.option(
    '-m',
    '--multi',
    is_flag=True,
    help='Treat the specified attributes as a list type.',
)
@click.pass_context
def update(ctx, attributes, hostname, id, site_id, attr_action, multi):
    """
    Update a Device.

    You must provide a Site ID using the -s/--site-id option.

    When updating a Device you must provide the unique ID (-i/--id) and at
    least one of the optional arguments.

    The -a/--attributes option may be provided multiple times, once for each
    key-value pair. You may also specify the -a a single time and separate
    key-value pairs by a single comma.

    When modifying attributes you have three actions to choose from:

    * Add (-A/--add-attributes). This is the default behavior that will add
    attributes if they don't exist, or update them if they do.

    * Delete (-d/--delete-attributes). This will cause attributes to be
    deleted. If combined with --multi the attribute will be deleted if either
    no value is provided, or if the attribute no longer contains a valid value.

    * Replace (-r/--replace-attributes). This will cause attributes to
    replaced. If combined with -m/--multi and multiple attributes of the same
    name are provided, only the last value provided will be used.
    """
    if not any([attributes, hostname]):
        msg = 'You must supply at least one of the optional arguments.'
        raise click.UsageError(msg)

    data = ctx.params
    ctx.obj.update(data)
