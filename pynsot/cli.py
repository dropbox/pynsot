# -*- coding: utf-8 -*-

"""
Command-line interface internals.
"""

import pynsot
from pynsot.client import Client
from pynsot.models import ApiModel
import argparse
import sys


# Used to map human-readable action names to API calls.
ACTION_MAP = {
    'add': 'post',
    'list': 'get',
    'remove': 'delete',
    'update': 'patch',
}


def parse_args(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser()
    parser.add_argument('--version', '-V', action='version',
            version='%(prog)s ' + pynsot.__version__)
    parser.add_argument('--verbose', '-v', action='store_true',
            help='toggle verbosity')

    subparsers = parser.add_subparsers(help='Help for objects',
                                       title='Objects',
                                       description='Valid objects')

    # Create the parser for sites. This is an example of how generation
    # of the parsers can be done using a factory method.
    parser_sites = subparsers.add_parser('sites', help='Sites')
    sites_subparsers = parser_sites.add_subparsers(help='Actions for network objects',
                                                title='Actions',
                                                description='Valid actions')
    sites_actions = {}
    for a in ACTION_MAP:
        sites_actions[a] = sites_subparsers.add_parser(a, help=a.title() + ' a site')
        sites_actions[a].add_argument('--name', '-n', type=str, help='Site name')  # , required=True)
        sites_actions[a].add_argument('--description', '-d', type=str, help='Site description')  # , required=True)
        sites_actions[a].set_defaults(which='sites.' + a)
        # Need a way to set required arguments on some args, something like,
        # although these are incorrect:
        #sites_actions['add'].name.required = True
        #sites_actions['add'].description.required = True

    #sites_actions['list'].add_argument('--id', '-i', type=int, help='Site id')

    # Create the parser for network
    parser_networks = subparsers.add_parser('networks', help='Network objects')
    parser_networks.add_argument('--cidr', '-c', type=str, help='Network address')

    parser_attributes = subparsers.add_parser('attributes', help='Attributes')
    #parser_devices = subparsers.add_parser('devices', help='Devices')
    #parser_users = subparsers.add_parser('users', help='Users')

    args = parser.parse_args(argv)
    return args


def main():
    args = parse_args()

    url = 'http://localhost:8990/api'
    email = 'jathan@localhost'

    api = Client(url, email=email)
    api._store['args'] = args

    args = api._store['args']
    # nsot sites add --name Bar --description 'Bar site'
    # => Namespace(description='Bar Site', name='Bar', verbose=False, which='sites.add')
    obj, action = args.which.split('.')  # => 'sites', 'add'
    api_method = getattr(api, obj)  # => api.sites
    api_verb = ACTION_MAP[action]  # => get
    api_call = getattr(api_method, api_verb)

    # Need a way to mapp these fields and
    skipped_args = ('verbose', 'which')
    data = {k: v for k, v in args.__dict__.items() if k not in skipped_args and v is not None}

    obj_single = obj[:-1]
    pretty_dict = ', '.join('%s=%r' % (k, v) for k, v in data.items())
    try:
        #print data
        #print api_method._store
        if action == 'list':
            result = api_call(**data)  # GET expects **kwargs
        else:
            result = api_call(data)  # POST/PATCH expects data=data
    except Exception as err:
        resp = getattr(err, 'response', None)
        if resp is not None:
            print 'FATAL', resp.status_code, resp.reason, 'trying to', action, obj_single, 'with args:', pretty_dict
        else:
            print 'FATAL', err
        sys.exit(2)

    # Add behavior
    if action == 'add':
        if result:
            m = ApiModel(result)
            print 'Successfully added %s (id: %d) with args: %s!' % (obj_single, m.id, pretty_dict)

    # List behavior
    elif action == 'list':
        if result:
            #print result
            import tabulate
            objects = result['data'][obj]
            headers = 'keys'
            tablefmt = 'simple'

            # TODO: make me a flag or something
            no_headers = False
            if no_headers:
                headers = []
                tablefmt = 'plain'

            print tabulate.tabulate(objects, headers=headers, tablefmt=tablefmt)
        else:
            print 'No %s found matching args: %s!' % (obj, pretty_dict)

    # And... scene.
    sys.exit(0)
