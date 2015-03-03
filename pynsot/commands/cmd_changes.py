# -*- coding: utf-8 -*-

"""
Sub-command for Changes.

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


# Ordered list of 2-tuples of (field, display_name) used to translate object
# field names oto their human-readable form when calling .print_list().
DISPLAY_FIELDS = (
    ('id', 'ID'),
    ('change_at', 'Change At'),
    ('event', 'Event'),
    ('resource_name', 'Resource'),
    ('user', 'User'),
    ('resource_id', 'R ID'),
    # ('site_id', 'Site ID'),
    # ('site', 'Site'),
)

VERBOSE_FIELDS = DISPLAY_FIELDS + (
    ('resource', 'Data'),
)



# Main group
@click.group()
@click.pass_context
def cli(ctx):
    """Change events."""


def transform_event(ctx, param, value):
    """Callback to transform event into title case."""
    if value is not None:
        return value.title()
    return value


def transform_resource_name(ctx, param, value):
    """Callback to transform resource_name into title case."""
    if value is not None:
        return value.title()
    return value


# List
@cli.command()
@click.option(
    '-e',
    '--event',
    metavar='EVENT',
    help='Filter result to specific event.',
    callback=transform_event,
)
@click.option(
    '-i',
    '--id',
    metavar='ID',
    help='Unique ID of the Change being retrieved.',
)
@click.option(
    '-l',
    '--limit',
    metavar='LIMIT',
    help='Limit result to N resources.',
)
@click.option(
    '-o',
    '--offset',
    metavar='OFFSET',
    help='Skip the first N resources.',
)
@click.option(
    '-R',
    '--resource-id',
    metavar='RESOURCE_ID',
    help='Filter to Changes for a specific resource ID (e.g. Network ID 1',
)
@click.option(
    '-r',
    '--resource-name',
    metavar='RESOURCE_NAME',
    help='Filter to Changes for a specific resource name (e.g. Network)',
    callback=transform_resource_name,
)
@click.option(
    '-s',
    '--site-id',
    metavar='SITE_ID',
    help='ID of the Site to retrieve Changes from.',
    required=True,
)
@click.pass_context
def list(ctx, event, id, limit, offset, resource_id, resource_name, site_id):
    """
    List existing Changes for a Site.

    You must provide a Site ID using the -s/--site-id option.

    When listing Changes, all objects are displayed by default. You may
    optionally lookup a single Change by ID using the -i/--id option.

    You may limit the number of results using the -l/--limit option.
    """
    data = ctx.params

    # If we provide ID, be verbose
    if id is not None:
        display_fields = VERBOSE_FIELDS
    else:
        display_fields = DISPLAY_FIELDS

    ctx.obj.list(data, display_fields=display_fields)
