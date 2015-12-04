"""
Callbacks used in handling command plugins.
"""

import ast
import csv
from itertools import chain
import logging

from ..vendor import click


log = logging.getLogger(__name__)

# Objects that do not have attribtues
NO_ATTRIBUTES = ('attributes',)

# Objects that support lookup by natural key
NATURAL_KEYS = {
    'devices': 'hostname',
    'networks': 'cidr'
}


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

    for obj in objects:
        constraints = {}
        for c_field in constraint_fields:
            try:
                constraints[c_field] = obj.pop(c_field)
            except KeyError:
                continue
        obj['constraints'] = constraints
    return data


def transform_attributes(ctx, param, value):
    """Callback to turn attributes arguments into a dict."""
    attrs = {}
    log.debug('TRANSFORM_ATTRIBUTES [IN]: %r' % (value,))

    # If this is a simple string, make it a list.
    if isinstance(value, basestring):
        value = [value]

    # Flatten the attributes in case any of them are comma-separated.
    values = [v.split(',') for v in value]
    items = set(chain.from_iterable(values))

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
        log.debug ('FILE ROW: %r', r)
        for k, v in r.iteritems():
            # Don't evaluate dicts
            if isinstance(v, dict):
                continue

            # Evaluate strings and if they are booleans, convert them.
            if not isinstance(v, basestring):
                msg = 'Error parsing file on line %d' % (lineno,)
                raise click.BadParameter(msg)
            if v.title() in ('True', 'False'):
                r[k] = ast.literal_eval(v)
        objects.append(r)

    log.debug('PARSED BULK DATA = %r' % (objects,))

    # Return a list of dicts
    return objects


def list_endpoint(ctx, display_fields, my_name=None):
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

    # Use our name, parent's command name, and the API object to retrieve the
    # endpoint resource used to call this endpoint.
    api = ctx.obj.api
    parent_name = ctx.obj.parent_name  # e.g. 'networks'

    if my_name is not None:
        ctx.obj.resource_name = my_name
    else:
        my_name = ctx.info_name  # e.g. 'supernets'

    # Make sure that parent_id is provided. This seems complicated because we
    # want to maintain dynamism across resource types.
    parent = None
    if parent_id is None:
        natural_key = NATURAL_KEYS.get(parent_name)

        # Look up the object by natural key (e.g. cidr)
        if natural_key is not None:
            parent = ctx.obj.get_single_object(data, natural_key)

        # If the object was found, get its id
        if parent is not None:
            parent_id = parent['id']

        # If it's not found, error out.
        if parent_id is None:
            raise click.UsageError(
                'No %s matching %s; try lookup using option "-i" / "--id".' %
                (parent_name, data.get(natural_key))
            )

    # e.g. /api/sites/1/networks/5/supernets/
    parent_resource = getattr(api, parent_name)
    my_resource = getattr(parent_resource(parent_id), my_name)

    ctx.obj.list(data, display_fields=display_fields, resource=my_resource)
