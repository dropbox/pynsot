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

from __future__ import unicode_literals

from ..vendor import click
from . import callbacks


__author__ = 'Jathan McCollum'
__maintainer__ = 'Jathan McCollum'
__email__ = 'jathan@dropbox.com'
__copyright__ = 'Copyright (c) 2015 Dropbox, Inc.'


# Ordered list of 2-tuples of (field, display_name) used to translate object
# field names oto their human-readable form when calling .print_list().
DISPLAY_FIELDS = (
    ('id', 'ID'),
    ('change_at', 'Change At'),
    ('user', 'User'),
    ('event', 'Event'),
    ('resource_name', 'Resource'),
    ('resource_id', 'Obj'),
    # ('site_id', 'Site ID'),
    # ('site', 'Site'),
)

# Fields to display when viewing a single record.
VERBOSE_FIELDS = (
    ('change_at', 'Change At'),
    ('user', 'User'),
    ('event', 'Event'),
    ('resource_name', 'Resource'),
    ('resource_id', 'ID'),
    ('resource', 'Data'),
)


# Main group
@click.group()
@click.pass_context
def cli(ctx):
    """
    Change events.

    All add, remove, and update events are logged as a Change. A Change
    includes information such as the change time, user, and the full resource
    after modification. Changes are immutable and can only be removed by
    deleting the entire Site.
    """


# List
@cli.command()
@click.option(
    '-e',
    '--event',
    metavar='EVENT',
    help='Filter result to specific event.',
    callback=callbacks.transform_event,
)
@click.option(
    '-i',
    '--id',
    metavar='ID',
    type=int,
    help='Unique ID of the Change being retrieved.',
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
    type=int,
    help='Skip the first N resources.',
)
@click.option(
    '-R',
    '--resource-id',
    metavar='RESOURCE_ID',
    type=int,
    help='Filter to Changes for a specific resource ID (e.g. Network ID 1)',
)
@click.option(
    '-r',
    '--resource-name',
    metavar='RESOURCE_NAME',
    help='Filter to Changes for a specific resource name (e.g. Network)',
    callback=callbacks.transform_resource_name,
)
@click.option(
    '-s',
    '--site-id',
    metavar='SITE_ID',
    type=int,
    help='Unique ID of the Site this Change is under.  [required]',
    callback=callbacks.process_site_id,
)
@click.pass_context
def list(ctx, event, id, limit, offset, resource_id, resource_name, site_id):
    """
    List Change events for a Site.

    You must provide a Site ID using the -s/--site-id option.

    When listing Changes, all events are displayed by default. You may
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
