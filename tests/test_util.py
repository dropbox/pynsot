# -*- coding: utf-8 -*-

"""
Test the utils lib.
"""

import pytest  # noqa

from pynsot.util import validate_cidr


def test_validate_cidr():
    """Test ``validate_cidr()``."""
    # IPv4
    assert validate_cidr('0.0.0.0/0')
    assert validate_cidr('1.2.3.4/32')

    # IPv6
    assert validate_cidr('::/0')
    assert validate_cidr('fe8::/10')

    # Bad
    assert not validate_cidr('bogus')
    assert not validate_cidr(None)
    assert not validate_cidr(object())
    assert not validate_cidr({})
    assert not validate_cidr([])
