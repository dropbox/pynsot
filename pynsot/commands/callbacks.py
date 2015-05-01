"""
Callbacks used in handling command plugins.
"""

import ast
import csv
import json
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
    constraints = {}
    for c_field in constraint_fields:
        constraints[c_field] = data.pop(c_field)
    data['constraints'] = constraints
    return data


def transform_attributes(ctx, param, value):
    """Callback to turn attributes arguments into a dict."""
    attrs = {}
    log.debug('TRANSFORM_ATTRIBUTES [IN]: %r' % (value,))

    # If value is a string, we'll assume that it's comma-separated.
    if isinstance(value, basestring):
        value = value.split(',')

    for attr in value:
        key, _, val = attr.partition('=')
        if not key:
            msg = 'Invalid attribute: %s; format should be key=value' % (attr,)
            raise click.UsageError(msg)
        try:
            val = json.loads(val)
        except ValueError:
            pass

        # Cast integers to strings (fix #24)
        if isinstance(val, int):
            val = str(val)

        log.debug(' name = %r', key)
        log.debug('value = %r', val)

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
    parent_name = ctx.obj.parent_name
    objects = []

    # Value is already an open file handle
    reader = csv.DictReader(value, delimiter=':')
    for r in reader:
        lineno = reader.line_num

        # Make sure the file is correctly formatted.
        if len(r) != len(reader.fieldnames):
            msg = 'File has wrong number of fields on line %d' % (lineno,)
            raise click.BadParameter(msg)

        # Transform attributes for eligible resource types
        if parent_name not in NO_ATTRIBUTES:
            attributes = transform_attributes(
                ctx, param, r['attributes']
            )
            r['attributes'] = attributes

        # Transform True, False into booleans
        for k, v in r.iteritems():
            if not isinstance(v, basestring):
                msg = 'Error parsing file on line %d' % (lineno,)
                raise click.BadParameter(msg)
            if v.title() in ('True', 'False'):
                r[k] = ast.literal_eval(v)
        objects.append(r)

    log.debug('PARSED BULK DATA = %r' % (objects,))

    # Return a dict keyed by calling object name
    return {parent_name: objects}


def list_endpoint(ctx, display_fields):
    """
    Determine params and a resource object to pass to ``ctx.obj.list()``

    :param ctx:
        Context from the calling command

    :param display_fields:
        Display fields used to list object results.
    """
    # Gather our args from our parent and ourself
    data = ctx.parent.params
    data.update(ctx.params)

    parent_id = data.pop('id')
    site_id = data.pop('site_id')

    # Make sure that parent_id is provided.
    if parent_id is None:
        raise click.UsageError('Missing option "-i" / "--id".')

    # Use our name, parent's command name, and the API object to retrieve the
    # endpoint resource used to call this endpoint.
    api = ctx.obj.api
    parent_name = ctx.obj.parent_name  # e.g. 'networks'
    my_name = ctx.info_name  # e.g. 'supernets'

    # e.g. /api/sites/1/networks/5/supernets
    parent_resource = getattr(api.sites(site_id), parent_name)
    my_resource = getattr(parent_resource(parent_id), my_name)

    ctx.obj.list(data, display_fields=display_fields, resource=my_resource)
