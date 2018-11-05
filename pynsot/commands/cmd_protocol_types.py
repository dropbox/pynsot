# -*- coding: utf-8 -*-

"""
Sub-command for Protocol Types.

In all cases ``data = ctx.params`` when calling the appropriate action method
on ``ctx.obj``. (e.g. ``ctx.obj.add(ctx.params)``)

Also, ``action = ctx.info_name`` *might* reliably contain the name of the
action function, but still not sure about that. If so, every function could be
fundamentally simplified to this::

    getattr(ctx.obj, ctx.info_name)(ctx.params)
"""

from __future__ import unicode_literals
import logging

from ..vendor import click
from . import callbacks, types

# Logger
log = logging.getLogger(__name__)

# Ordered list of 2-tuples of (field, display_name) used to translate object
# field names oto their human-readable form when calling .print_list().
DISPLAY_FIELDS = (
    ('id', 'ID'),
    ('name', 'Name'),
    ('description', 'Description'),
    ('required_attributes', 'Required Attributes'),
)

# Fields to display when viewing a single record.
VERBOSE_FIELDS = (
    ('id', 'ID'),
    ('name', 'Name'),
    ('description', 'Description'),
    ('required_attributes', 'Required Attributes'),
    ('site', 'Site ID'),
)


# Main group
@click.group()
@click.pass_context
def cli(ctx):
    """
    Protocol Type objects.

    A Protocol Type resource can represent a network protocol type (e.g. bgp,
    is-is, ospf, etc.)

    Protocol Types can have any number of required attributes as defined below.
    """


# Add
@cli.command()
@click.option(
    '-r',
    '--required-attributes',
    metavar='ATTRIBUTE',
    type=str,
    help=('''The name of a Protocol attribute. This option can be providedi
           multiple times, once per attribute.'''),
    multiple=True,
)
@click.option(
    '-d',
    '--description',
    metavar='DESCRIPTION',
    type=str,
    help='The description for this Protocol Type.',
)
@click.option(
    '-n',
    '--name',
    metavar='NAME',
    type=str,
    help='The name of the Protocol Type.',
    required=True,
)
@click.option(
    '-s',
    '--site-id',
    metavar='SITE_ID',
    type=int,
    help='Unique ID of the Site this Protocol Type is under.  [required]',
    callback=callbacks.process_site_id,
)
@click.pass_context
def add(ctx, required_attributes, description, name, site_id):
    """
    Add a new Protocol Type.

    You must provide a Protocol Type name or ID using the UPDATE option.

    When adding a new Protocol Type, you must provide a value for the -n/--name
    option.

    Examples: OSPF, BGP, etc.

    You may also provide required Protocol attributes, you may specify the
    -r/--required-attributes option once for each attribute. The Protocol
    attributes must exist before adding them to a protocol type.

    You must provide a Site ID using the -s/--site-id option.
    """
    data = ctx.params

    # Remove if empty; allow default assignment
    if description is None:
        data.pop('description')

    ctx.obj.add(data)


# List
@cli.group(invoke_without_command=True)
@click.option(
    '-d',
    '--description',
    metavar='DESCRIPTION',
    type=str,
    help='Filter by Protocol Type matching this description.',
)
@click.option(
    '-i',
    '--id',
    metavar='ID',
    type=types.NATURAL_KEY,
    help='Unique ID of the Protocol Type being retrieved.',
)
@click.option(
    '-l',
    '--limit',
    metavar='LIMIT',
    type=int,
    help='Limit result to N resources.',
)
@click.option(
    '-n',
    '--name',
    metavar='NAME',
    help='Filter to Protocol Type matching this name.'
)
@click.option(
    '-o',
    '--offset',
    metavar='OFFSET',
    help='Skip the first N resources.',
)
@click.option(
    '-s',
    '--site-id',
    metavar='SITE_ID',
    help='Unique ID of the Site this Protocol Type is under.',
    callback=callbacks.process_site_id,
)
@click.pass_context
def list(ctx, description, id, limit, name, offset, site_id):
    """
    List existing Protocol Types for a Site.

    You must provide a Site ID using the -s/--site-id option.

    When listing Protocol Types, all objects are displayed by default. You
    optionally may lookup a single Protocol Types by ID using the -i/--id
    option. The ID can either be the numeric ID of the Protocol Type.
    """
    data = ctx.params

    # If we provide ID, show more fields
    if any([id, name]):
        display_fields = VERBOSE_FIELDS
    else:
        display_fields = DISPLAY_FIELDS

    # If we aren't passing a sub-command, just call list(), otherwise let it
    # fallback to default behavior.
    if ctx.invoked_subcommand is None:
        ctx.obj.list(
            data, display_fields=display_fields,
            verbose_fields=VERBOSE_FIELDS
        )


# Remove
@cli.command()
@click.option(
    '-i',
    '--id',
    metavar='ID',
    type=types.NATURAL_KEY,
    help='Unique ID of the Protocol Type being deleted.',
    required=True,
)
@click.option(
    '-s',
    '--site-id',
    metavar='SITE_ID',
    type=int,
    help='Unique ID of the Site this Protocol Type is under.',
    callback=callbacks.process_site_id,
)
@click.pass_context
def remove(ctx, id, site_id):
    """
    Remove an Protocol Type.

    You must provide a Site ID using the -s/--site-id option.

    When removing an Protocol Type, you must provide the ID of the Protocol
    Type using -i/--id.

    You may retrieve the ID for an Protocol Type by parsing it from the list of
    Protocol Types for a given Site:

      nsot protocol_types list --site-id <site_id> | grep <protocol_type name>
    """
    data = ctx.params
    ctx.obj.remove(**data)


# Update
@cli.command()
@click.option(
    '-r',
    '--required-attributes',
    metavar='ATTRIBUTE',
    type=str,
    help=('''The name of a Protocol attribute. This option can be provided multiple
         times, once per attribute.'''),
    multiple=True,
    callback=callbacks.transform_attributes,
)
@click.option(
    '-d',
    '--description',
    metavar='DESCRIPTION',
    type=str,
    help='The description for this Protocol Type.',
)
@click.option(
    '-i',
    '--id',
    metavar='ID',
    type=types.NATURAL_KEY,
    help='Unique ID of the Protocol Type being updated.',
    required=True,
)
@click.option(
    '-n',
    '--name',
    metavar='NAME',
    type=str,
    help='The name of the Protocol Type.',
)
@click.option(
    '-s',
    '--site-id',
    metavar='SITE_ID',
    type=int,
    help='Unique ID of the Site this Protocol Type is under.',
    callback=callbacks.process_site_id,
)
@click.pass_context
def update(ctx, required_attributes, description, id, name, site_id):
    """
    Update an Protocol Type.

    You must provide a Site ID using the -s/--site-id option.

    When updating an Protocol Type you must provide the ID (-i/--id). The ID
    can either be the numeric ID of the Protocol Type or the name.

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
    data = ctx.params
    ctx.obj.update(data)
