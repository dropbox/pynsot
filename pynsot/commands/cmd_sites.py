# -*- coding: utf-8 -*-

"""
Sub-command for Sites.

In all cases ``data = ctx.params`` when calling the appropriate action method
on ``ctx.obj``. (e.g. ``ctx.obj.add(ctx.params)``)

Also, ``action = ctx.info_name`` *might* reliably contain the name of the
action function, but still not sure about that. If so, every function could be
fundamentally simplified to this::

    getattr(ctx.obj, ctx.info_name)(ctx.params)
"""

from __future__ import unicode_literals

from ..vendor import click


__author__ = 'Jathan McCollum'
__maintainer__ = 'Jathan McCollum'
__email__ = 'jathan@dropbox.com'
__copyright__ = 'Copyright (c) 2015 Dropbox, Inc.'


# Ordered list of 2-tuples of (field, display_name) used to translate object
# field names oto their human-readable form when calling .print_list().
DISPLAY_FIELDS = (
    ('id', 'ID'),
    ('name', 'Name'),
    ('description', 'Description'),
)


# Main group
@click.group()
@click.pass_context
def cli(ctx):
    """
    Site objects.

    Sites are the top-level resource from which all other resources descend. In
    other words, Sites contain Attributes, Changes, Devices, and Networks.

    Sites function as unique namespaces that can contain other resources. Sites
    allow an organization to have multiple instances of potentially conflicting
    resources. This could be beneficial for isolating corporeate vs. production
    environments, or pulling in the IP space of an acquisition.
    """


# Add
@cli.command()
@click.option(
    '-d',
    '--description',
    default='',
    metavar='DESC',
    help='A helpful description for the Site.',
)
@click.option(
    '-n',
    '--name',
    metavar='NAME',
    help='The name of the Site.',
    required=True,
)
@click.pass_context
def add(ctx, description, name):
    """
    Add a new Site.

    When adding a Site, you must provide a name using the -n/--name option.

    You may provide a helpful description for the Site using the
    -d/--description option.
    """
    data = ctx.params
    ctx.obj.add(data)


# List
@cli.command()
@click.option(
    '-i',
    '--id',
    metavar='ID',
    type=int,
    help='Unique ID of the Site to retrieve.',
)
@click.option(
    '-l',
    '--limit',
    metavar='LIMIT',
    type=int,
    help='Limit results to N resources.',
)
@click.option(
    '-n',
    '--name',
    metavar='NAME',
    help='Filter by Site name.'
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
    type=int,
    help='Skip the first N resources.',
)
@click.pass_context
def list(ctx, id, limit, name, natural_key, offset):
    """
    List existing Sites.

    When listing Sites, all objects are displayed by default. You may
    optionally lookup a single Site by name using the -n/--name option or by ID
    using the -i/--id option.

    You may limit the number of results using the -l/--limit option.

    NOTE: The -i/--id option will take precedence causing all other options
    to be ignored.
    """
    data = ctx.params
    ctx.obj.list(data, display_fields=DISPLAY_FIELDS)


# Remove
@cli.command()
@click.option(
    '-i',
    '--id',
    metavar='ID',
    type=int,
    help='Unique ID of the Site that should be removed.',
    required=True,
)
@click.pass_context
def remove(ctx, id):
    """
    Remove a Site.

    When removing a site, you must provide the unique ID using -i/--id. You may
    retrieve the ID for a Site by looking it up by name using:

        nsot sites list --name <name>
    """
    data = ctx.params
    ctx.obj.remove(**data)


# Update
@cli.command()
@click.option(
    '-d',
    '--description',
    metavar='DESC',
    help='A helpful description for the Site.',
)
@click.option(
    '-i',
    '--id',
    metavar='ID',
    type=int,
    help='Unique ID of the Site that should be updated.',
    required=True,
)
@click.option(
    '-n',
    '--name',
    metavar='NAME',
    help='The name of the Site.',
)
@click.pass_context
def update(ctx, description, id, name):
    """
    Update a Site.

    When updating a Site you must provide the unique ID (-i/--id) and at least
    one of the -n/--name or -d/--description arguments.
    """
    if name is None and description is None:
        msg = 'You must supply at least one of -n/--name or -d/--description'
        raise click.UsageError(msg)

    data = ctx.params
    ctx.obj.update(data)
