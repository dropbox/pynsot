# -*- coding: utf-8 -*-

"""
Command-line interface internals.
"""

import pynsot
from pynsot.client import Client
import argparse
import sys


def parse_args(argv=None):
    if argv is None:
        argv = sys.argv[1:]
        print argv

    parser = argparse.ArgumentParser()
    parser.add_argument('--version', '-V', action='version',
            version='%(prog)s ' + pynsot.__version__)
    parser.add_argument('--verbose', '-v', action='store_true',
            help='toggle verbosity')

    subparsers = parser.add_subparsers(help='Help for objects',
                                       title='Objects',
                                       description='Valid objects')

    # Create the parser for network
    parser_network = subparsers.add_parser('networks', help='Network objects')
    parser_network.add_argument('--address', '-a', type=str,
            help='Network address')

    attribute_parser = subparsers.add_parser('attributes', help='Attributes')
    device_parser = subparsers.add_parser('devices', help='Devices')
    user_parser = subparsers.add_parser('users', help='Users')

    args = parser.parse_args(argv)
    return args


def main():
    args = parse_args()
    print args
