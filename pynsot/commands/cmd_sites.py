# -*- coding: utf-8 -*-

"""
Sub-command for sites.

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


import click


# Fields to display when printing a list of items
DISPLAY_FIELDS = ('id', 'name', 'description')


# Main group
@click.group()
@click.pass_context
def cli(ctx):
    """Site objects."""
    if ctx.obj.verbose:
        print 'I am:', ctx.info_name
        print 'my parent is:', ctx.parent.info_name


# Add
@cli.command()
@click.option('-n', '--name', metavar='NAME', help='Site name', required=True)
@click.option('-d', '--description', metavar='DESC', help='Site description',
              required=True)
@click.pass_context
def add(ctx, name, description):
    """
    Add a new site.

    When adding a new site, you must provide values for both the -n/--name and
    -d/--description arguments.
    """
    data = ctx.params
    ctx.obj.add(data)


# List
@cli.command()
@click.option('-n', '--name', metavar='NAME', help='Filter by site name.')
@click.option('-l', '--limit', metavar='LIMIT', help='Number of items.')
@click.pass_context
def list(ctx, name, limit):
    """
    List existing sites.

    When listing sites, all sites are displayed by default. You may optionally
    lookup a single site by name using the -n/--name argument.

    You may limit the number of results using the -l/--limit argument.

    """
    data = ctx.params
    ctx.obj.list(data, fields=DISPLAY_FIELDS)


# Remove
@cli.command()
@click.option('-i', '--id', metavar='ID', help='Unique ID for site',
              required=True)
@click.pass_context
def remove(ctx, id):
    """
    Remove a site.

    When removing a site, you must provide the unique ID using -i/--id. You may
    retrieve the id for a site by looking it up by name using:

        nsot sites list --name <name>
    """
    data = ctx.params
    ctx.obj.remove(**data)


# Update
@cli.command()
@click.option('-i', '--id', metavar='ID', help='Unique ID for site',
              required=True)
@click.option('-n', '--name', metavar='NAME', help='Site name')
@click.option('-d', '--description', metavar='DESC', help='Site description')
@click.pass_context
def update(ctx, id, name, description):
    """
    Update a site.

    When updating a site you must provide the unique ID (-i/--id) and at least
    one of the -n/--name or -d/--description arguments.
    """
    if name is None and description is None:
        msg = 'You must supply at least one of --name or --description'
        raise click.UsageError(msg)

    data = ctx.params
    ctx.obj.update(data)
