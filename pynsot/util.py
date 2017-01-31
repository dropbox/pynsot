# -*- coding: utf-8 -*-

"""
Utilities and stuff.
"""

from __future__ import unicode_literals

from .vendor import netaddr


def get_result(response):
    """
    Get the desired result from an API response.

    :param response: Requests API response object
    """
    try:
        payload = response.json()
    except AttributeError:
        payload = response

    if 'results' in payload:
        return payload['results']

    # Or just return the payload... (next-gen)
    return payload


def validate_cidr(cidr):
    """
    Return whether ``cidr`` is valid.

    :param cidr:
        IPv4/IPv6 address
    """
    try:
        netaddr.IPNetwork(cidr)
    except (TypeError, netaddr.AddrFormatError):
        return False
    else:
        return True


def dict_to_cidr(obj):
    """
    Take an dict of a Network object and return a cidr-formatted string.

    :param obj:
        Dict of an Network object
    """
    return '%s/%s' % (obj['network_address'], obj['prefix_length'])


def slugify(s):
    """
    Slugify a string for use in URLs. This mirrors ``nsot.util.slugify()``.

    :param s:
        String to slugify
    """

    disallowed_chars = ['/']
    replacement = '_'

    for char in disallowed_chars:
        s = s.replace(char, replacement)

    return s
