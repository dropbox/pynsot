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
