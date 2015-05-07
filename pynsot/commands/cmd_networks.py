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
    ('network_address', 'Network'),
    ('prefix_length', 'Prefix'),
    # ('site_id': 'Site ID'),
    ('is_ip', 'Is IP?'),
    ('ip_version', 'IP Ver.'),
    ('parent_id', 'Parent ID'),
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
    '-s',
    '--site-id',
    metavar='SITE_ID',
    type=int,
    help='Unique ID of the Site this Network is under.  [required]',
    callback=callbacks.process_site_id,
)
@click.pass_context
def add(ctx, attributes, bulk_add, cidr, site_id):
    """
    Add a new Network.

    You must provide a Site ID using the -s/--site-id option.

    When adding a new Network, you must provide a value for the -c/--cidr
    option.

    If you wish to add attributes, you may specify the -a/--attributes
    option once for each key/value pair.
    """
    data = bulk_add or ctx.params

    # Enforce required options
    if bulk_add is None:
        if cidr is None:
            raise click.UsageError('Missing option "-c" / "--cidr"')
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
    default=False,
    show_default=True,
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
    '-s',
    '--site-id',
    metavar='SITE_ID',
    help='Unique ID of the Site this Network is under.  [required]',
    callback=callbacks.process_site_id,
)
@click.pass_context
def list(ctx, attributes, cidr, id, include_ips, include_networks, limit,
         network_address, offset, prefix_length, query, root_only, site_id):
    """
    List existing Networks for a Site.

    You must provide a Site ID using the -s/--site-id option.

    When listing Networks, all objects are displayed by default. You optionally
    may lookup a single Network by ID using the -i/--id option.

    You may limit the number of results using the -l/--limit option.
    """
    data = ctx.params

    # If we aren't passing a sub-command, just call list(), otherwise let it
    # fallback to default behavior.
    if ctx.invoked_subcommand is None:
        if query:
            results = ctx.obj.api.sites(site_id).networks.query.get(**data)
            objects = results['data']['networks']
            # log.debug('QUERY OBJECTS = %r' % (objects,))
            networks = sorted(
                '%s/%s' % (d['network_address'], d['prefix_length'])
                for d in objects
            )
            click.echo('\n'.join(networks))
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
    callbacks.list_endpoint(ctx, display_fields=DISPLAY_FIELDS)


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
    callbacks.list_endpoint(ctx, display_fields=DISPLAY_FIELDS)


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
    '-i',
    '--id',
    metavar='ID',
    type=int,
    help='Unique ID of the Network being updated.',
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
def update(ctx, attributes, id, site_id):
    """
    Update a Network.

    You must provide a Site ID using the -s/--site-id option.

    When updating a Network you must provide the unique ID (-i/--id) and at
    least one of the optional arguments.
    """
    if not any([attributes]):
        msg = 'You must supply at least one of the optional arguments.'
        raise click.UsageError(msg)

    data = ctx.params
    ctx.obj.update(data)
