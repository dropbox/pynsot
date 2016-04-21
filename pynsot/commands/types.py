# -*- coding: utf-8 -*-

"""
Custom Click parameter types.
"""

from __future__ import unicode_literals

from ..vendor import click
from ..util import validate_cidr


class NetworkIdParamType(click.ParamType):
    """Custom paramer type that supports Network ID or CIDR."""
    name = 'network identifier'

    def convert(self, value, param, ctx):
        if value is None:
            return

        tests = [int, validate_cidr]
        win = False
        for test in tests:
            try:
                win = test(value)
            except:
                pass
            else:
                if not win:
                    continue
                return value

        else:
            self.fail('%s is not an valid integer or CIDR' % value, param, ctx)

    def __repr__(self):
        return 'NETWORK_ID'

NETWORK_ID = NetworkIdParamType()
