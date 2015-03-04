# -*- coding: utf-8 -*-

"""
Sub-command for Attributes.

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
from . import callbacks


# Ordered list of 2-tuples of (field, display_name) used to translate object
# field names oto their human-readable form when calling .print_list().
DISPLAY_FIELDS = (
    ('id', 'ID'),
    ('name', 'Name'),
    ('resource_name', 'Resource'),
    # ('site_id': 'Site ID'),
    ('required', 'Required?'),
    ('display', 'Display?'),
    ('multi', 'Multi?'),
    ('description', 'Description'),
)


# Main group
@click.group()
@click.pass_context
def cli(ctx):
    """Attribute objects."""


# Add
@cli.command()
@click.option(
    '-d',
    '--description',
    metavar='DESC',
    help='A helpful description of the Attribute.',
)
@click.option(
    '--display',
    help='Whether this Attribute should be be displayed by default in UIs.',
    is_flag=True,
)
@click.option(
    '--multi',
    help='Whether the attribute should be treated as a list type.',
    is_flag=True,
)
@click.option(
    '-n',
    '--name',
    metavar='NAME',
    help='The name of the Attribute',
    required=True,
)
@click.option(
    '--required',
    help='Whether this Attribute should be required.',
    is_flag=True,
)
@click.option(
    '-r',
    '--resource-name',
    metavar='RESOURCE',
    help='The type of resource this Attribute is for (e.g. Network)',
    required=True,
    callback=callbacks.transform_resource_name,
)
@click.option(
    '-s',
    '--site-id',
    metavar='SITE_ID',
    help='Unique ID of the Site this Attribute is under.  [required]',
    callback=callbacks.process_site_id,
)
@click.pass_context
def add(ctx, description, display, multi, name, resource_name, required,
        site_id):
    """
    Add a new Attribute.

    You must provide a Site ID using the -s/--site-id option.

    When adding a new Attribute, you must provide a value for the -n/--name
    and -r/--resource-name options.
    """
    data = ctx.params
    ctx.obj.add(data)


# List
@cli.command()
@click.option(
    '-i',
    '--id',
    metavar='ID',
    help='Unique ID of the Attribute being retrieved.',
)
@click.option(
    '--display/--no-display',
    help='Filter to Attributes meant to be displayed.',
    default=None,
)
@click.option(
    '-l',
    '--limit',
    metavar='LIMIT',
    help='Limit result to N resources.',
)
@click.option(
    '--multi/--no-multi',
    help='Filter on whether Attributes are list type or not.',
    default=None,
)
@click.option(
    '-n',
    '--name',
    metavar='NAME',
    help='Filter to Attribute with this name.',
)
@click.option(
    '-o',
    '--offset',
    metavar='OFFSET',
    help='Skip the first N resources.',
)
@click.option(
    '--required/--no-required',
    help='Filter to Attributes that are required.',
    default=None,
)
@click.option(
    '-r',
    '--resource-name',
    metavar='RESOURCE',
    help='Filter to Attributes for a specific resource (e.g. Network)',
    callback=callbacks.transform_resource_name,
)
@click.option(
    '-s',
    '--site-id',
    metavar='SITE_ID',
    help='Unique ID of the Site this Attribute is under.  [required]',
    callback=callbacks.process_site_id,
)
@click.pass_context
def list(ctx, id, display, limit, multi, name, offset, required, resource_name,
         site_id):
    """
    List existing Attributes for a Site.

    You must provide a Site ID using the -s/--site-id option.

    When listing Attributes, all objects are displayed by default. You may
    optionally lookup a single Attribute by name using the -n/--name option or
    by ID using the -i/--id option.

    You may limit the number of results using the -l/--limit option.
    """
    data = ctx.params
    ctx.obj.list(data, display_fields=DISPLAY_FIELDS)


# Remove
@cli.command()
@click.option(
    '-i',
    '--id',
    metavar='ID',
    help='Unique ID of the Attribute being deleted.',
    required=True,
)
@click.option(
    '-s',
    '--site-id',
    metavar='SITE_ID',
    help='Unique ID of the Site this Attribute is under.  [required]',
    callback=callbacks.process_site_id,
)
@click.pass_context
def remove(ctx, id, site_id):
    """
    Remove an Attribute.

    You must provide a Site ID using the -s/--site-id option.

    When removing an Attribute, you must provide the unique ID using -i/--id.
    You may retrieve the ID for an Attribute by looking it up by name for a
    given Site:

        nsot attributes list --name <name> --site <site_id>
    """
    data = ctx.params
    ctx.obj.remove(**data)


# Update
@cli.command()
@click.option(
    '-d',
    '--description',
    metavar='DESC',
    help='A helpful description of the Attribute.',
)
@click.option(
    '--display/--no-display',
    help='Whether this Attribute should be be displayed by default in UIs.',
    default=None,
)
@click.option(
    '-i',
    '--id',
    metavar='ID',
    help='Unique ID of the Attribute being updated.',
    required=True,
)
@click.option(
    '--multi/--no-multi',
    help='Whether the Attribute should be treated as a list type.',
    default=None,
)
@click.option(
    '--required/--no-required',
    help='Whether this Attribute should be required.',
    default=None,
)
@click.option(
    '-s',
    '--site-id',
    metavar='SITE_ID',
    help='Unique ID of the Site this Attribute is under.  [required]',
    callback=callbacks.process_site_id,
)
@click.pass_context
def update(ctx, description, display, id, multi, required, site_id):
    """
    Update an Attribute.

    You must provide a Site ID using the -s/--site-id option.

    When updating an Attribute you must provide the unique ID (-i/--id) and at
    least one of the optional arguments.
    """
    click.echo(ctx.params)
    optional = (description, display, multi, required)
    provided = []
    for opt in optional:
        if opt in (True, False) or isinstance(opt, basestring):
            provided.append(opt)

    # If none of them were provided, complain.
    if not provided:
        msg = 'You must supply at least one the optional arguments.'
        raise click.UsageError(msg)

    data = ctx.params
    ctx.obj.update(data)
