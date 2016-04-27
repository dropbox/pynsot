# -*- coding: utf-8 -*-

"""
Callbacks used in handling command plugins.
"""

from __future__ import unicode_literals
import ast
import csv
import logging

from ..vendor import click


log = logging.getLogger(__name__)

# Objects that do not have attribtues
NO_ATTRIBUTES = ('attributes',)


def process_site_id(ctx, param, value):
    """
    Callback to attempt to get site_id from ``~/.pynsotrc`` if it's not
    provided using -s/--site-id.
    """
    log.debug('GOT DEFAULT_SITE: %s' % ctx.obj.api.default_site)
    log.debug('GOT PROVIDED SITE_ID: %s' % value)

    # Try to get site_id from the app config, or complain that it's not set.
    if value is None:
        default_site = ctx.obj.api.default_site
        if default_site is None:
            raise click.UsageError('Missing option "-s" / "--site-id".')
        value = default_site
    else:
        log.debug('Setting provided site_id as default_site.')
        ctx.obj.api.default_site = value
    return value


def process_constraints(data, constraint_fields):
    """
    Callback to move constrained fields from incoming data into a 'constraints'
    key.

    :param data:
        Incoming argument dict

    :param constraint_fields:
        Constrained fields to move into 'constraints' dict
    """
    # Always use a list so that we can handle bulk operations
    objects = data if isinstance(data, list) else [data]

    # Enforce that pattern is a string.
    if data['pattern'] is None:
        data['pattern'] = ''

    for obj in objects:
        constraints = {}
        for c_field in constraint_fields:
            try:
                c_value = obj.pop(c_field)
            except KeyError:
                continue
            else:
                # If the value is not set, translate it to False
                if c_value is None:
                    c_value = False
                constraints[c_field] = c_value
        obj['constraints'] = constraints
    return data


def transform_attributes(ctx, param, value):
    """Callback to turn attributes arguments into a dict."""
    attrs = {}
    log.debug('TRANSFORM_ATTRIBUTES [IN]: %r' % (value,))

    # If this is a simple string, make it a list.
    if isinstance(value, basestring):
        value = [value]

    # Flatten the attributes using a set to eliminate any duplicates.
    items = set(value)

    # Prepare the context object for storing attribute actions
    parent = ctx.find_root()
    if not hasattr(parent, '_attributes'):
        parent._attributes = []

    for attr in items:
        key, _, val = attr.partition('=')
        if not key:
            msg = 'Invalid attribute: %s; format should be key=value' % (attr,)
            raise click.UsageError(msg)

        # Cast integers to strings (fix #24)
        if isinstance(val, int):
            val = str(val)

        log.debug(' name = %r', key)
        log.debug('value = %r', val)
        parent._attributes.append((key, val))
        attrs[key] = val

    log.debug('TRANSFORM_ATTRIBUTES [OUT]: %r' % (attrs,))
    return attrs


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


def process_bulk_add(ctx, param, value):
    """
    Callback to parse bulk addition of objects from a colon-delimited file.

    Format:

    + The first line of the file must be the field names.
    + Attribute pairs must be commma-separated, and in format k=v
    + The attributes must exist!
    """
    if value is None:
        return value

    # This is our object name (e.g. 'devices')
    parent_resource_name = ctx.obj.parent_resource_name
    objects = []

    # Value is already an open file handle
    reader = csv.DictReader(value, delimiter=b':')
    for row in reader:
        lineno = reader.line_num

        # Make sure the file is correctly formatted.
        if len(row) != len(reader.fieldnames):
            msg = 'File has wrong number of fields on line %d' % (lineno,)
            raise click.BadParameter(msg)

        # Transform attributes for eligible resource types
        if parent_resource_name not in NO_ATTRIBUTES:
            # FIXME(jathan): This IS going to break at some point. We need to
            # considered how to take in complex a/v pairs in this context.
            # Naively split on ',' for now.
            incoming_attributes = row['attributes'].split(',')
            outgoing_attributes = transform_attributes(
                ctx, param, incoming_attributes
            )
            row['attributes'] = outgoing_attributes

        # Transform True, False into booleans
        log.debug('FILE ROW: %r', row)
        for key, val in row.iteritems():
            # Don't evaluate dicts
            if isinstance(val, dict):
                continue

            # Evaluate strings and if they are booleans, convert them.
            if not isinstance(val, basestring):
                msg = 'Error parsing file on line %d' % (lineno,)
                raise click.BadParameter(msg)
            if val.title() in ('True', 'False'):
                row[key] = ast.literal_eval(val)
        objects.append(row)

    log.debug('PARSED BULK DATA = %r' % (objects,))

    # Return a list of dicts
    return objects


def get_resource_by_natural_key(ctx, data, resource_name, resource=None):
    """
    Attempt to return the reource_id for an object.

    :param ctx:
        Context from the calling command

    :param data:
        Query parameters used for object lookup

    :param resource_name:
        The API resource name (for display)

    :param resource:
        The API resource client object
    """
    resource_id = None
    obj = None

    # Look up the object by natural key (e.g. cidr)
    obj = ctx.obj.get_single_object(data, resource=resource)

    # If the object was found, get its id
    if obj is not None:
        resource_id = obj['id']

    # If it's not found, error out.
    if resource_id is None:
        raise click.UsageError(
            'No matching %s found; try lookup using option "-i" / "--id".' %
            (resource_name,)
        )

    return resource_id


def list_subcommand(ctx, display_fields=None, my_name=None, grep_name=None,
                    with_parent=True, return_results=False):
    """
    Determine params and a resource object to pass to ``ctx.obj.list()``

    This is used for mapping sub-commands to nested API resources.

    For example::

        nsot networks list -s 1 -c 10.0.0.0/8 subnets

    Would be mapped to::

        GET /api/sites/1/networks/5/subnets/

    If ``return_results`` is set, ``data`` will be to ``ctx.obj.detail()``
    and the results will be directly returned instead.

    :param ctx:
        Context from the calling command

    :param display_fields:
        Display fields used to list object results.

    :param my_name:
        (Optional) Overload the App's resource_name to match this value

    :param grep_name:
        (Optional) Overload the App's grep_name to match this value

    :param with_parent:
        Whether to treat the nested lookup as a detail view (default) using the
        parent resource id, or as a list view without an id lookup.

    :param return_results:
        Whether to pass the results to ``list()`` or pass them to ``detail()``
        and return them.
    """
    if display_fields is None and not return_results:
        raise SyntaxError(
            'Display fields must be provided when not returning results.'
        )

    # Gather our args from our parent and ourself
    data = ctx.parent.params
    data.update(ctx.params)

    # This will be used for resource lookup for detail routes.
    parent_resource_id = data.pop('id')

    # Prepare the app and rebase the API to include site_id.
    app = ctx.obj
    app.rebase(data)

    # Use our name, parent's command name, and the API object to retrieve the
    # endpoint resource used to call this endpoint.
    parent_resource_name = app.parent_resource_name  # e.g. 'networks'

    # If we've provided my_name, overload the App's resource_name to match
    # it.
    if my_name is None:
        my_name = ctx.info_name  # e.g. 'supernets'

    # e.g. /api/sites/1/networks/
    parent_resource = getattr(app.api, parent_resource_name)

    # Make sure that parent_resource_id is provided. This seems complicated
    # because we want to maintain dynamism across resource types.
    if with_parent:
        if parent_resource_id is None:
            parent_resource_id = get_resource_by_natural_key(
                ctx, data, parent_resource_name, parent_resource
            )

        # e.g. /api/sites/1/networks/5/supernets/
        my_resource = getattr(parent_resource(parent_resource_id), my_name)

    # Otherwise, just treat this as a list endpoint with no parent lookup.
    else:
        my_resource = getattr(parent_resource, my_name)

    app.resource_name = my_name
    app.grep_name = grep_name or my_name

    # If return_results, just pass data to my_resource.get() and return
    # whatever comes back.
    if return_results:
        return app.detail(data, resource=my_resource)

    app.list(data, display_fields=display_fields, resource=my_resource)
