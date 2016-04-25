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

from __future__ import unicode_literals
import logging

from ..vendor import click
from . import callbacks


log = logging.getLogger(__name__)

# Ordered list of 2-tuples of (field, display_name) used to translate object
# field names oto their human-readable form when calling .print_list().
DISPLAY_FIELDS = (
    ('id', 'ID'),
    ('name', 'Name'),
    ('resource_name', 'Resource'),
    ('required', 'Required?'),
    ('multi', 'Multi?'),
    ('description', 'Description'),
)

# Fields to display when viewing a single record.
VERBOSE_FIELDS = (
    ('id', 'ID'),
    ('name', 'Name'),
    ('resource_name', 'Resource'),
    ('required', 'Required?'),
    ('display', 'Display?'),
    ('multi', 'Multi?'),
    ('constraints', 'Constraints'),
    ('description', 'Description'),
)

# Sub-fields for Attribute constraints
CONSTRAINT_FIELDS = ('allow_empty', 'pattern', 'valid_values')


# Main group
@click.group()
@click.pass_context
def cli(ctx):
    """
    Attribute objects.

    Attributes are arbitrary key/value pairs that can be assigned to various
    resources. If an attribute is required then additions/updates for that
    resource will require that attribute be present. Existing resources will
    not be forcefully validated until update.
    """


# Add
@cli.command()
@click.option(
    '--allow-empty',
    help='Constrain whether to allow this Attribute to have an empty value.',
    is_flag=True,
)
@click.option(
    '-b',
    '--bulk-add',
    metavar='FILENAME',
    help='Bulk add Attributes from the specified colon-delimited file.',
    type=click.File('rb'),
    callback=callbacks.process_bulk_add,
)
@click.option(
    '-d',
    '--description',
    default='',
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
    help='The name of the Attribute.  [required]',
)
@click.option(
    '-p',
    '--pattern',
    help='Constrain attribute values to this regex pattern.',
    default=None,
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
    help='The resource type this Attribute is for (e.g. Device).  [required]',
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
@click.option(
    '-V',
    '--valid-values',
    metavar='VALUE',
    help=(
        'Constrain valid values for this Attribute. May be specified '
        'multiple times.'
    ),
    multiple=True,
)
@click.pass_context
def add(ctx, allow_empty, bulk_add, description, display, multi, name, pattern,
        resource_name, required, valid_values, site_id):
    """
    Add a new Attribute.

    You must provide a Site ID using the -s/--site-id option.

    When adding a new Attribute, you must provide a value for the -n/--name
    and -r/--resource-name options.
    """
    data = bulk_add or ctx.params

    # Enforce required options
    if bulk_add is None:
        if name is None:
            raise click.UsageError('Missing option "-n" / "--name".')
        if resource_name is None:
            raise click.UsageError('Missing option "-r" / "--resource-name".')

    # Handle the constraint fields
    data = callbacks.process_constraints(
        data, constraint_fields=CONSTRAINT_FIELDS
    )
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
    type=int,
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
    type=int,
    help='Unique ID of the Site this Attribute is under.  [required]',
    callback=callbacks.process_site_id,
)
@click.pass_context
def list(ctx, id, display, limit, multi, name, natural_key, offset, required,
         resource_name, site_id):
    """
    List existing Attributes for a Site.

    You must provide a Site ID using the -s/--site-id option.

    When listing Attributes, all objects are displayed by default. You may
    optionally lookup a single Attribute by name using the -n/--name option or
    by ID using the -i/--id option.

    You may limit the number of results using the -l/--limit option.
    """
    data = ctx.params

    # If we provide ID, be verbose
    if id is not None or all([name, resource_name]):
        display_fields = VERBOSE_FIELDS
    else:
        display_fields = DISPLAY_FIELDS

    ctx.obj.list(
        data, display_fields=display_fields, verbose_fields=VERBOSE_FIELDS
    )


# Remove
@cli.command()
@click.option(
    '-i',
    '--id',
    metavar='ID',
    type=int,
    help='Unique ID of the Attribute being deleted.',
    required=True,
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
    '--allow-empty/--no-allow-empty',
    help='Constrain whether to allow this Attribute to have an empty value.',
    default=None,
)
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
    type=int,
    help='Unique ID of the Attribute being updated.',
)
@click.option(
    '--multi/--no-multi',
    help='Whether the Attribute should be treated as a list type.',
    default=None,
)
@click.option(
    '-n',
    '--name',
    metavar='NAME',
    help='The name of the Attribute.',
)
@click.option(
    '-p',
    '--pattern',
    help='Constrain attribute values to this regex pattern.',
    default=None,
)
@click.option(
    '--required/--no-required',
    help='Whether this Attribute should be required.',
    default=None,
)
@click.option(
    '-r',
    '--resource-name',
    metavar='RESOURCE',
    help='The resource type this Attribute is for (e.g. Device).',
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
@click.option(
    '-V',
    '--valid-values',
    metavar='VALUE',
    help=(
        'Constrain valid values for this Attribute. May be specified '
        'multiple times.'
    ),
    multiple=True,
)
@click.pass_context
def update(ctx, allow_empty, description, display, id, multi, name, pattern,
           required, resource_name, site_id, valid_values):
    """
    Update an Attribute.

    You must provide a Site ID using the -s/--site-id option.

    When updating an Attribute you may either provide the unique ID (-i/--id)
    OR you may provide the name (-n/--name) and resource_name
    (-r/--resource-name) together in lieu of ID to uniquely identify the
    attribute. You must also provide at least one of the optional arguments.

    The values for name (-n/--name) and resource_name (-r/--resource-name)
    cannot be updated and are used for object lookup only.

    If any of the constraints are supplied (--allow-empty/--no-allow-empty,
    -p/--pattern, -v/--valid-values) ALL constraint values will be initialized
    unless explicitly provided. (This is currently a limitation in the server
    API that will be addressed in a future release.)
    """
    # If name or resource_name are provided, both must be provided
    if (name and not resource_name) or (resource_name and not name):
        raise click.UsageError(
            '-n/--name and -r/--resource-name must be provided together.'
        )

    # Otherwise ID must be provided.
    elif (not name and not resource_name) and not id:
        raise click.UsageError('Missing option "-i" / "--id".')

    # One of the optional arguments must be provided (non-False) to proceed.
    optional_args = ('allow_empty', 'description', 'display', 'multi',
                     'pattern', 'required', 'valid_values')
    provided = []
    for opt in optional_args:
        val = ctx.params[opt]

        # If a flag is provided or a param is a string (e.g. pattern), or if
        # it's a tuple with 1 or more item, it's been provided.
        if any([
            val in (True, False),
            isinstance(val, basestring),
            (isinstance(val, tuple) and len(val) > 0)
        ]):
            provided.append(opt)

    # If none of them were provided, complain.
    if not provided:
        raise click.UsageError(
            'You must supply at least one the optional arguments.'
        )

    # Only update the constraints if any of them are updated. Otherwise leave
    # them alone.
    if any([
        allow_empty is not None,
        isinstance(pattern, basestring),
        valid_values
    ]):
        log.debug('Constraint field provided; updating constraints...')
        data = callbacks.process_constraints(
            ctx.params, constraint_fields=CONSTRAINT_FIELDS
        )
    else:
        data = ctx.params

    ctx.obj.update(data)
