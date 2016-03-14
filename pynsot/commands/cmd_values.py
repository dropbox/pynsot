# -*- coding: utf-8 -*-

"""
Sub-command for Values.

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
__copyright__ = 'Copyright (c) 2016 Dropbox, Inc.'


# Ordered list of 2-tuples of (field, display_name) used to translate object
# field names oto their human-readable form when calling .print_list().
DISPLAY_FIELDS = (
    ('name', 'Name'),
    ('value', 'Value'),
    ('resource_name', 'Resource'),
    ('resource_id', 'Resource ID'),
    # ('site_id': 'Site ID'),
)

# Fields to display when viewing a single record.
VERBOSE_FIELDS = (
    ('id', 'ID'),
    ('name', 'Name'),
    ('value', 'Value'),
    ('resource_name', 'Resource'),
    ('resource_id', 'Resource ID'),
    ('attribute', 'Attribute'),
)


# Main group
@click.group()
@click.pass_context
def cli(ctx):
    """
    Value objects.

    Values are assigned by Attribute to various resource objects.
    """


# List
@cli.command()
@click.option(
    '-n',
    '--name',
    metavar='NAME',
    required=True,
    help='Filter to Attribute with this name.',
)
@click.option(
    '-r',
    '--resource-name',
    metavar='RESOURCE_NAME',
    help='Filter to Values for a specific resource name (e.g. Device)',
    callback=callbacks.transform_resource_name,
)
@click.option(
    '-s',
    '--site-id',
    metavar='SITE_ID',
    type=int,
    help='Unique ID of the Site this Attribute is under.  [required]',
    callback=callbacks.process_site_id,
)
@click.pass_context
def list(ctx, name, resource_name, site_id):
    """
    List existing Values by Attribute name for a Site.

    You must provide a Name using the -n/--name option.

    You must provide a Site ID using the -s/--site-id option.

    When listing Values, all matching Attributes across all resource types are
    returned by default. You may optionally filter by a single resource name by
    using the -r/--resource-name option.
    """
    data = ctx.params

    # Fetch the matching values directly from the API client, filter
    # duplicates, and sort the output.
    results = ctx.obj.api.sites(site_id).values.get(**data)
    values = {d['value'] for d in results}
    click.echo('\n'.join(sorted(values)))
