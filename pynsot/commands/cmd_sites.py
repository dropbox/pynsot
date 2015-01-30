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


# Main group
@click.group()
@click.pass_context
def cli(ctx):
    """Site objects"""
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
    """Add a site"""
    data = ctx.params
    ctx.obj.add(data)


# List
@cli.command()
@click.option('-n', '--name', metavar='NAME', help='Filter by site name')
@click.pass_context
def list(ctx, name):
    """List sites"""
    data = ctx.params
    ctx.obj.list(data)


# Remove
@cli.command()
@click.option('-i', '--id', metavar='ID', help='Unique ID for site',
              required=True)
@click.pass_context
def remove(ctx, id):
    """Remove a site"""
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
    """Update a site"""
    if name is None and description is None:
        msg = 'You must supply at least one of --name or --description'
        raise click.UsageError(msg)

    data = ctx.params
    ctx.obj.update(data)
