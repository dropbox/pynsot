# -*- coding: utf-8 -*-

"""
Sub-command for Networks.

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


__author__ = 'Jathan McCollum'
__maintainer__ = 'Jathan McCollum'
__email__ = 'jathan@dropbox.com'
__copyright__ = 'Copyright (c) 2015-2016 Dropbox, Inc.'


# Ordered list of 2-tuples of (field, display_name) used to translate object
# field names oto their human-readable form when calling .print_list().
DISPLAY_FIELDS = (
    ('id', 'ID'),
    ('network_address', 'Network'),
    ('prefix_length', 'Prefix'),
    # ('site_id': 'Site ID'),
    ('is_ip', 'Is IP?'),
    ('ip_version', 'IP Ver.'),
    ('parent_id', 'Parent ID'),
    ('state', 'State'),
    ('attributes', 'Attributes'),
)


# Main group
@click.group()
@click.pass_context
def cli(ctx):
    """
    Network objects.

    A Network resource can represent an IP Network and an IP Address. Working
    with networks is usually done with CIDR notation.

    Networks can have any number of arbitrary attributes as defined below.
    """


# Add
@cli.command()
@click.option(
    '-a',
    '--attributes',
    metavar='ATTRS',
    help='A key/value pair attached to this Network (format: key=value).',
    multiple=True,
    callback=callbacks.transform_attributes,
)
@click.option(
    '-b',
    '--bulk-add',
    metavar='FILENAME',
    help='Bulk add Networks from the specified colon-delimited file.',
    type=click.File('rb'),
    callback=callbacks.process_bulk_add,
)
@click.option(
    '-c',
    '--cidr',
    metavar='CIDR',
    help='A network or IP address in CIDR notation.  [required]',
)
@click.option(
    '-S',
    '--state',
    metavar='STATE',
    type=str,
    help='The allocation state of the Network.',
)
@click.option(
    '-s',
    '--site-id',
    metavar='SITE_ID',
    type=int,
    help='Unique ID of the Site this Network is under.  [required]',
    callback=callbacks.process_site_id,
)
@click.pass_context
def add(ctx, attributes, bulk_add, cidr, state, site_id):
    """
    Add a new Network.

    You must provide a Site ID using the -s/--site-id option.

    When adding a new Network, you must provide a value for the -c/--cidr
    option.

    If you wish to add attributes, you may specify the -a/--attributes
    option once for each key/value pair.
    """
    data = bulk_add or ctx.params

    # Additional handling for non-bulk requests only, as bulk_add is a list
    if bulk_add is None:
        # Required option
        if cidr is None:
            raise click.UsageError('Missing option "-c" / "--cidr"')
        # Remove if empty, allow default assignment
        if state is None:
            data.pop('state', None)
    ctx.obj.add(data)


# List
@cli.group(invoke_without_command=True)
@click.option(
    '-a',
    '--attributes',
    metavar='ATTRS',
    help='A key/value pair attached to this Network (format: key=value).',
    multiple=True,
)
@click.option(
    '-c',
    '--cidr',
    metavar='CIDR',
    help=(
        'Filter to Networks matching this CIDR. If provided, this overrides '
        '-n/--network-address and -p/--prefix-length.'
    ),
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
    '-i',
    '--id',
    metavar='ID',
    type=int,
    help='Unique ID of the Network being retrieved.',
)
@click.option(
    '--include-networks/--no-include-networks',
    is_flag=True,
    help='Include/exclude non-IP networks.',
    default=True,
    show_default=True,
)
@click.option(
    '--include-ips/--no-include-ips',
    is_flag=True,
    help='Include/exclude IP addresses.',
    default=True,
    show_default=True,
)
@click.option(
    '-V',
    '--ip-version',
    metavar='IP_VERSION',
    type=click.Choice(['4', '6']),
    help='Filter to Networks matchin this IP version.',
)
@click.option(
    '-l',
    '--limit',
    metavar='LIMIT',
    help='Limit result to N resources.',
)
@click.option(
    '-n',
    '--network-address',
    metavar='NETWORK',
    help='Filter to Networks matching this network address.',
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
    '-p',
    '--prefix-length',
    metavar='PREFIX',
    type=int,
    help='Filter to Networks matching this prefix length.',
)
@click.option(
    '-q',
    '--query',
    metavar='QUERY',
    help='Perform a set query using Attributes and output matching Networks.',
)
@click.option(
    '-r',
    '--root-only',
    is_flag=True,
    help='Filter to root Networks.',
    default=False,
    show_default=True,
)
@click.option(
    '-S',
    '--state',
    metavar='STATE',
    type=str,
    help='The allocation state of the Network.',
)
@click.option(
    '-s',
    '--site-id',
    metavar='SITE_ID',
    help='Unique ID of the Site this Network is under.  [required]',
    callback=callbacks.process_site_id,
)
@click.pass_context
def list(ctx, attributes, cidr, delimited, grep, id, include_ips,
         include_networks, ip_version, limit, network_address, natural_key,
         offset, prefix_length, query, root_only, state, site_id):
    """
    List existing Networks for a Site.

    You must provide a Site ID using the -s/--site-id option.

    When listing Networks, all objects are displayed by default. You optionally
    may lookup a single Network by ID using the -i/--id option.

    You may limit the number of results using the -l/--limit option.
    """
    data = ctx.params
    data.pop('delimited')  # We don't want this going to the server.

    # If we aren't passing a sub-command, just call list(), otherwise let it
    # fallback to default behavior.
    if ctx.invoked_subcommand is None:
        if query:
            results = ctx.obj.api.sites(site_id).networks.query.get(**data)
            networks = sorted(
                (d['network_address'], d['prefix_length']) for d in results
            )
            networks = ['%s/%s' % obj for obj in networks]
            joiner = ',' if delimited else '\n'
            click.echo(joiner.join(networks))
        else:
            ctx.obj.list(data, display_fields=DISPLAY_FIELDS)


@list.command()
@click.option(
    '-d',
    '--direct',
    is_flag=True,
    help='Return only direct subnets.',
    default=False,
    show_default=True,
)
@click.pass_context
def subnets(ctx, *args, **kwargs):
    """Get subnets of a Network."""
    callbacks.list_subcommand(ctx, display_fields=DISPLAY_FIELDS)


@list.command()
@click.option(
    '-d',
    '--direct',
    is_flag=True,
    help='Return only direct supernets.',
    default=False,
    show_default=True,
)
@click.pass_context
def supernets(ctx, *args, **kwargs):
    """Get supernets of a Network."""
    callbacks.list_subcommand(ctx, display_fields=DISPLAY_FIELDS)


# Remove
@cli.command()
@click.option(
    '-i',
    '--id',
    metavar='ID',
    type=int,
    help='Unique ID of the Network being deleted.',
    required=True,
)
@click.option(
    '-s',
    '--site-id',
    metavar='SITE_ID',
    type=int,
    help='Unique ID of the Site this Network is under.  [required]',
    callback=callbacks.process_site_id,
)
@click.pass_context
def remove(ctx, id, site_id):
    """
    Remove a Network.

    You must provide a Site ID using the -s/--site-id option.

    When removing a Network, you must provide the unique ID using -i/--id. You
    may retrieve the ID for a Network by parsing it from the list of Networks
    for a given Site:

        nsot networks list --site-id <site_id> | grep <network>
    """
    data = ctx.params
    ctx.obj.remove(**data)


# Update
@cli.command()
@click.option(
    '-a',
    '--attributes',
    metavar='ATTRS',
    help='A key/value pair attached to this Network (format: key=value).',
    multiple=True,
    callback=callbacks.transform_attributes,
)
@click.option(
    '-c',
    '--cidr',
    metavar='CIDR',
    help=(
        'A network or IP address in CIDR notation. Used for lookup only in '
        'place of -i/--id!'
    )
)
@click.option(
    '-i',
    '--id',
    metavar='ID',
    type=int,
    help='Unique ID of the Network being updated.',
)
@click.option(
    '-s',
    '--site-id',
    metavar='SITE_ID',
    type=int,
    help='Unique ID of the Site this Network is under.  [required]',
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
        'Causes attributes to be replaced instead of updated. If combined '
        'with --multi, the entire list will be replaced.'
    ),
)
@click.option(
    '-m',
    '--multi',
    is_flag=True,
    help='Treat the specified attributes as a list type.',
)
@click.option(
    '-S',
    '--state',
    metavar='STATE',
    type=str,
    help='The allocation state of the Network.',
)
@click.pass_context
def update(ctx, attributes, cidr, id, site_id, attr_action, multi, state):
    """
    Update a Network.

    You must provide a Site ID using the -s/--site-id option.

    When updating a Network you must provide either the unique ID (-i/--id) or
    CIDR (-c/--cidr) and at least one of the optional arguments. If -i/--id is
    provided -c/--cidr will be ignored.

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
    if not any([attributes, state]):
        msg = 'You must supply at least one of the optional arguments.'
        raise click.UsageError(msg)

    if not id and not cidr:
        raise click.UsageError(
            'You most provide -c/--cidr when not providing -i/--id.'
        )

    data = ctx.params
    ctx.obj.update(data)
