"""
Callbacks used in handling command plugins.
"""

import click
import logging


log = logging.getLogger(__name__)


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
            raise click.UsageError('Missing option "-s" / "--site-id"')
        value = default_site

    return value


def transform_attributes(ctx, param, value):
    """Callback to turn attributes arguments into a dict."""
    attrs = {}
    for attr in value:
        key, _, val = attr.partition('=')
        if not all([key, val]):
            msg = 'Invalid attribute: %s; format should be key=value' % (attr,)
            raise click.UsageError(msg)
        attrs[key] = val
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
