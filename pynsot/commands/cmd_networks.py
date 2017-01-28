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
from . import callbacks, types


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

# Commands that have been deprecated/renamed and which will display a warning
# to the user if specified. A sub-command must use the DeprecatedAliasGroup
# class for this to take effect. See below: list()
DEPRECATED_COMMANDS = {
    'descendents': 'descendants'
}


# TODO(jathan): Move this somewhere else at such point we have other commands
# that require deprecated aliases.
class DeprecatedAliasGroup(click.Group):
    """
    Group which will warn a user if a specified command is deprecated.
    """
    def get_command(self, ctx, cmd_name):
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv

        match = DEPRECATED_COMMANDS.get(cmd_name)
        if not match:
            return None

        # If there's a match, warn the user that it's deprecated.
        click.echo(
            click.style('[WARNING] ', fg='yellow') +
            '%s has been deprecated. Use %s instead.' %
            (cmd_name, match)
        )
        return click.Group.get_command(self, ctx, match)


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

        # Remove if empty; allow default assignment
        if state is None:
            data.pop('state', None)

    ctx.obj.add(data)


# List (aliased to notify users of deprecated commands)
@cli.group(cls=DeprecatedAliasGroup, invoke_without_command=True)
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
        if query is not None:
            ctx.obj.set_query(data, delimited)
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
    """Get subnets of a network."""
    callbacks.list_subcommand(
        ctx, display_fields=DISPLAY_FIELDS, grep_name='networks'
    )


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
    """Get supernets of a network."""
    callbacks.list_subcommand(
        ctx, display_fields=DISPLAY_FIELDS, grep_name='networks'
    )


@list.command()
@click.pass_context
def parent(ctx, *args, **kwargs):
    """Get parent network of a network."""
    callbacks.list_subcommand(
        ctx, display_fields=DISPLAY_FIELDS, grep_name='networks'
    )


@list.command()
@click.option(
    '--ascending',
    is_flag=True,
    help='Display results in ascending order.',
    default=False,
    show_default=True,
)
@click.pass_context
def ancestors(ctx, *args, **kwargs):
    """Recursively get all parents of a network."""
    callbacks.list_subcommand(
        ctx, display_fields=DISPLAY_FIELDS, grep_name='networks'
    )


@list.command()
@click.pass_context
def children(ctx, *args, **kwargs):
    """Get immediate children of a network."""
    callbacks.list_subcommand(
        ctx, display_fields=DISPLAY_FIELDS, grep_name='networks'
    )


@list.command()
@click.pass_context
def descendants(ctx, *args, **kwargs):
    """Recursively get all children of a network."""
    callbacks.list_subcommand(
        ctx, display_fields=DISPLAY_FIELDS, grep_name='networks'
    )


@list.command()
@click.pass_context
def root(ctx, *args, **kwargs):
    """Get parent of all ancestors of a network."""
    callbacks.list_subcommand(
        ctx, display_fields=DISPLAY_FIELDS, grep_name='networks'
    )


@list.command()
@click.option(
    '--include-self',
    is_flag=True,
    help='Whether to include this Network in output.',
    default=False,
    show_default=True,
)
@click.pass_context
def siblings(ctx, *args, **kwargs):
    """Get networks with same parent as a network."""
    callbacks.list_subcommand(
        ctx, display_fields=DISPLAY_FIELDS, grep_name='networks'
    )


@list.command(
    short_help='Get the closest matching parent of a network.'
)
@click.pass_context
def closest_parent(ctx, *args, **kwargs):
    """
    Get the closest matching parent of a Network even if it doesn't exist in
    the database.
    """
    # FIXME(jathan): This is a workaround until we remove the natural_key
    # machinery that predates the builtin support for natural_key lookups on
    # the backend from the CLI app.
    data = ctx.parent.params
    obj_id = data.get('id')
    cidr = data.get('cidr')
    if obj_id is not None or cidr is None:
        raise click.UsageError(
            '-i/--id is invalid for this subcommand. Use -c/--cidr.'
        )

    data['id'] = data['cidr']
    # End workaround

    callbacks.list_subcommand(
        ctx, display_fields=DISPLAY_FIELDS, grep_name='networks'
    )


# The fields we want to display for assignments.
ASSIGNMENT_FIELDS = (
    ('id', 'ID'),
    ('hostname', 'Hostname'),
    ('interface_name', 'Interface'),
)


@list.command()
@click.pass_context
def assignments(ctx, *args, **kwargs):
    """Get interface assignments for a network."""
    callbacks.list_subcommand(
        ctx, display_fields=ASSIGNMENT_FIELDS, grep_name='assignments'
    )


# Reserved method
@list.command()
@click.pass_context
def reserved(ctx, *args, **kwargs):
    """Get all reserved networks."""
    data = ctx.parent.params
    data['id'] = 1  # FIXME(jathan): Hack so app.get_single_object() suceeds.
    callbacks.list_subcommand(
        ctx, display_fields=DISPLAY_FIELDS, grep_name='networks',
        with_parent=False
    )


# Allocation methods
@list.command()
@click.option(
    '-n',
    '--num',
    metavar='NUM',
    type=int,
    help='Number of Networks to return.'
)
@click.option(
    '-p',
    '--prefix-length',
    metavar='PREFIX',
    type=int,
    help='Return Networks matching this prefix length.',
    required=True
)
@click.option(
    '-s',
    '--strict-allocation',
    metavar='STRICT_ALLOCATION',
    is_flag=True,
    help='Return Networks can be strictly allocated'
)
@click.pass_context
def next_network(ctx, *args, **kwargs):
    """
    Get next available networks for a network.
    """
    results = callbacks.list_subcommand(ctx, return_results=True)
    click.echo('\n'.join(results))


@list.command()
@click.option(
    '-n',
    '--num',
    metavar='NUM',
    type=int,
    help='Number of addresses to return.'
)
@click.option(
    '-s',
    '--strict-allocation',
    metavar='STRICT_ALLOCATION',
    is_flag=True,
    help='Return Networks can be strictly allocated'
)
@click.pass_context
def next_address(ctx, *args, **kwargs):
    """
    Get next available addresses for a network.
    """
    results = callbacks.list_subcommand(ctx, return_results=True)
    click.echo('\n'.join(results))


# Remove
@cli.command()
@click.option(
    '-c',
    '--cidr',
    'id',
    metavar='CIDR',
    help='CIDR if the Network being deleted.',
)
@click.option(
    '-i',
    '--id',
    metavar='ID',
    type=types.NETWORK_ID,
    help='Unique ID or CIDR of the Network being deleted.',
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

    When removing a Network, you must either provider the unique ID using
    -i/--id, or the CIDR of the Network using -c/--cidr.

    If both are provided, -c/--cidr will be ignored.
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
def update(ctx, attributes, cidr, id, state, site_id, attr_action, multi):
    """
    Update a Network.

    You must provide a Site ID using the -s/--site-id option.

    When updating a Network you must provide either the unique ID (-i/--id) or
    CIDR (-c/--cidr) and at least one of the optional arguments. If -i/--id is
    provided -c/--cidr will be ignored.

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
    if not any([attributes, state]):
        msg = 'You must supply at least one of the optional arguments.'
        raise click.UsageError(msg)

    if not id and not cidr:
        raise click.UsageError(
            'You must provide -c/--cidr when not providing -i/--id.'
        )

    data = ctx.params
    ctx.obj.update(data)
