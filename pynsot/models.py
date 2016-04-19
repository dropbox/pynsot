# -*- coding: utf-8 -*-

'''API Model Classes

These resource models are derrived from collections.MutableMapping and, thus,
act like dicts and can instantiate with raw resource output from API as well as
simplifying by providing site_id and (usually) the natural key (cidr, hostname,
etc).

Example
-------

>>> from pynsot.models import Network, Device, Interface
>>> from pynsot.client import get_api_client
>>> client = get_api_client()
>>> net = Network(raw=client.networks.get()[-1])
>>>
>>> # Or also...
>>> # >>> net = Network(client=client, site_id=1, cidr='8.8.8.0/24')
>>>
>>> net.exists()
>>> True
>>>
>>> net.existing_resource()
{u'attributes': {},
 u'id': 81,
 u'ip_version': u'4',
 u'is_ip': False,
 u'network_address': u'254.0.0.0',
 u'parent_id': 1,
 u'prefix_length': 24,
 u'site_id': 1,
 u'state': u'allocated'}
>>>
>>> net.purge()
True
>>>
>>> net.exists()
False
>>>
>>> net.ensure()
True
>>>
>>> net.exists()
True
>>>
>>> net['site_id']
2
>>>
>>> net['site_id'] = 4
>>>
>>> net.exists()
False
>>>
>>> net['site_id'] = 2
>>>
>>> net.exists()
True
'''

from __future__ import unicode_literals
import logging
import collections
from abc import abstractproperty, abstractmethod, ABCMeta
from netaddr import IPNetwork
from pynsot.util import get_result
from pynsot.client import get_api_client


class Resource(collections.MutableMapping):
    '''Base API Abstraction Models Class

    Instances of an API abstraction model represent a single NSoT resource and
    provide methods for managing the state of it upstream. They can be
    instantiated by the raw returned object from NSoT API or more simply by a
    few descriptive kwargs.

    Resource is a subclass of :class:``collections.MutableMapping`` which makes
    it act as a dictionary would. The mapping represents the payload that would
    be accepted by NSoT and can be manipulated as desired like a normal dict.

    Subclassing:
        Subclasses must adhere to a simple contract:
            * Overload the abstractmethods and abstractproperties this class
              uses
            * If custom arguments are needed, overload ``self.postinit``.
              Just make sure to call ``self.init_payload()`` at the end. All
              kwargs that aren't handled by ``self.__init__`` are passed here

    :param site_id: Site ID this reseource belongs to. Required unless ``raw``
        is supplied.
    :type site_id: int
    :param attributes: Attributes to add to resource. If supplying ``raw``, add
        these after the instantiation like:

            >>> obj = Device(raw=RAW_API_DICT)
            >>> obj['attributes'] = {}

    :type attributes: dict
    :param client: Pynsot client for API interactions. Will be lazily loaded if
        not provided, but might be cheaper to supply it up front.
    :type client: pynsot.client.BaseClient
    :param raw: Raw NSoT resource object. What would be returned from a GET,
        POST, PUT, or PATCH operation for a single resource. Gets mapped
        directly to payload
    :type raw: dict
    '''

    __metaclass__ = ABCMeta

    def __init__(
        self,
        site_id=None,
        client=None,
        raw=None,
        attributes=None,
        **kwargs
    ):
        if raw is None:
            raw = {}
        if attributes is None:
            attributes = {}

        self.logger = logging.getLogger(__name__)
        self.errors = []
        self.last_error = None
        # Placeholder for .existing_resource() state
        self._existing_resource = {}
        self._payload = {}
        # Parameter validations

        # Site ID is required but can come from either kwarg or raw resource
        # dict, latter being preferred.
        if raw.get('site_id'):
            site_id = raw['site_id']
        elif site_id:
            pass  # Already set
        else:
            raise TypeError(
                'Resource requires site_id via param or ``raw`` key'
            )

        self._site_id = site_id
        self.client = client
        self.raw = raw
        self.attributes = attributes

        if not self.raw:
            self.postinit(**kwargs)
        else:
            # This is done here because subclases do this in their postinit().
            # If raw is passed, there's no reason to go through the postinit
            # process which takes things like network_address, hostname, etc.
            #
            # Every subclasses init_payload method has a condition for 'if raw
            # set raw' basically.
            self.init_payload()

    def postinit(self, **kwargs):
        '''Overloadable method for post __init__

        Use this for things that need to happen post-init, including
        subclass-specific argument handling.

        This method is called at the very end of __init__ unless ``raw`` is
        given.

        :params kwargs: All unhandled kwargs from __init__ are passed here
        :type kwargs: dict
        '''
        # If not being overloaded by subclass, still need to call this required
        # method if ``raw`` isn't provided
        self.init_payload()
        pass

    def ensure_client(self, **kwargs):
        '''Ensure that object has a client object

        Client may be passed during __init__ as a kwarg, but call this before
        doing any client work to ensure

        :param kwargs: These will be passed to get_api_client.
        :type kwargs: dict
        '''
        if self.client:
            return
        else:
            self.client = get_api_client(**kwargs)

    @abstractproperty
    def identifier(self):
        '''Human-friendly string to represent the resource

        Used in log messages and magic methods for comparison. Examples here
        would be CIDR, hostname, etc

        :rtype: str
        '''
        pass

    @property
    def resource(self):
        '''Pynsot client for resource type

        :rtype: pynsot.client.BaseClient
        '''
        self.ensure_client()
        return getattr(self.client, self.resource_name)

    @abstractproperty
    def resource_name(self):
        '''Name of resource

        Must be plural

        :rtype: str
        '''
        pass

    @abstractmethod
    def init_payload(self):
        '''
        Initializes the payload dictionary using resource specific data
        '''
        pass

    @property
    def payload(self):
        '''Represents exact payload sent to NSoT server

        :returns: _payload
        :rtype: dict
        '''
        return self._payload

    @payload.setter
    def payload(self, value):
        '''Setter for payload'''
        self._payload = value

    def __iter__(self):
        '''Iterate through payload keys'''
        return iter(self.payload)

    def __getitem__(self, key):
        '''Get item from payload'''
        return self.payload[key]

    def __setitem__(self, key, value):
        '''Set item in payload

        Cache is cleared here since the current resource has changed
        '''
        self.clear_cache()
        self.payload[key] = value

    def __delitem__(self, key):
        '''Delete item from payload

        Cache is cleared here since the current resource has changed
        '''
        self.clear_cache()
        del self.payload[key]

    def __len__(self):
        return len(self._payload)

    def __repr__(self):
        '''Human-friendly representation'''
        title = self.resource_name[:-1].title()
        return '<%s: %s>' % (title, str(self))

    def __str__(self):
        return str(self.identifier)

    def __eq__(self, other):
        '''Using ``identifier`` and ``site_id``, compare to another resource'''
        try:
            x = '%s:%s' % (self.identifier, self._site_id)
            y = '%s:%s' % (other.identifier, other._site_id)
            return x == y
        except:
            raise TypeError('Other object is not a Resource type')

    def log_error(self, error):
        '''Log and append errors to object

        This does a check to see if response object available from HTTP
        request. If not, that's OK too and it'll just append the raw error.
        '''
        if hasattr(error, 'response') and hasattr(error.response, 'json'):
            try:
                meta = error.response.json()
            except:
                meta = error.response
        else:
            meta = error

        self.logger.debug(
            '[%s] %s' % (self.identifier, meta),
            exc_info=True,
        )
        self.logger.warning(
            '[%s] %s' % (self.identifier, meta),
        )
        self.errors.append(meta)
        self.last_error = meta

    def existing_resource(self):
        '''Returns upstream resource

        If nothing exists, empty dict is returned. The result of this is cached
        in a property (_existing_resource) for cheaper re-checks. This can be
        cleared via ``.clear_cache()``

        :rtype: dict
        '''
        self.ensure_client()
        if self._existing_resource:
            return self._existing_resource
        else:
            cur = dict(self)
            cur.pop('attributes', None)
            # We pop attributes because the query fails leaving them in
            try:
                # Site client of resource type because NSoT doesn't support
                # passing site_id as a query parameter
                site = getattr(
                    self.client.sites(self['site_id']),
                    self.resource_name,
                )
                lookup = get_result(site.get(**cur))
            except Exception as e:
                self.log_error(e)
                # There might be a better way to do this. If the NSoT server is
                # unreachable or otherwise the lookup fails it'll log properly
                # and return as if nothing exists. If the resource actually
                # exists but due to reachability it couldn't confirm some
                # action may be unnecessarily took user-side.
                #
                # Honestly, though, I think this is a decent trade-off
                self._existing_resource = {}
                return self._existing_resource

            existing = len(lookup) > 0
            if existing:
                # This is where state will be kept for this
                self._existing_resource = lookup[0]
                return self._existing_resource
            else:
                self._existing_resource = {}
                return self._existing_resource

    def clear_cache(self):
        '''Clears state of certain properties

        This is ideally done during a write operation against the API, such as
        ``.purge()`` or ``.ensure()``. Helps prevent representing out-of-date
        information
        '''
        self._existing_resource = {}

    def exists(self):
        '''Does the current resource exist?

        :rtype: bool
        '''
        return bool(self.existing_resource())

    def ensure(self):
        '''Ensure object in current state exists in NSoT

        By site, make sure resource exists. True if it is or was able to get to
        the desired state, False if not and logged in ``last_error``.

        Having this operation be done individually for each resource
        has some pros and cons. Generally as long as the amount of items
        is small enough, it's not a huge difference but it is an extra
        HTTP request.

        Sending in bulk halts at the first error and fails the following
        so it requires more handling.

        Cache is cleared first thing and before return.

        :rtype: bool
        '''
        self.clear_cache()
        to_ensure = dict(self)

        try:
            # PATCH instead of POST
            if self.exists() and self.resource_name != 'interfaces':
                self.logger.debug('[%s] Patching', self.identifier)
                to_ensure['id'] = self.existing_resource()['id']
                self.resource.patch([to_ensure])
                self.logger.info('[%s] has been patched!', self.identifier)
                self.clear_cache()
                return True

            else:  # POST for initially creating
                self.logger.debug('[%s] Creating', self.identifier)
                self.resource.post([to_ensure])
                self.logger.info('[%s] has been created!', self.identifier)
                return True
        except Exception as e:
            self.log_error(e)
            self.clear_cache()
            return False

    def purge(self):
        '''Ensure resource doesn't exist upstream

        By site, make sure resource is deleted. True if it is or was able to
        get to the desired state, False if not and logged in ``last_error``.

        Cache is cleared first thing and before return.

        :rtype: bool
        '''
        self.clear_cache()
        try:
            if self.exists():
                self.logger.debug('[%s] Deleting', self.identifier)
                id_ = self.existing_resource()['id']
                self.resource(id_).delete()
                self.logger.info('[%s] has been deleted!', self.identifier)
                self.clear_cache()
                return True

            else:
                # We should return True to show the state is already how we
                # want it to be. False should be for unable to ensure resource
                # is gone
                return True
        except Exception as e:
            self.log_error(e)
            self.clear_cache()
            return False


class Network(Resource):
    '''Network API Abstraction Model

    Subclass of Resource.

    >>> n = Network(cidr='8.8.8.0/24', site_id=1)
    >>> n.exists()
    False
    >>> n.ensure()
    True
    >>> n.exists()
    True
    >>> n.existing_resource()
    {u'attributes': {},
     u'id': 31,
     u'ip_version': u'4',
     u'is_ip': True,
     u'network_address': u'8.8.8.0',
     u'parent_id': 1,
     u'prefix_length': 24,
     u'site_id': 1,
     u'state': u'assigned'}
    >>>
    >>> n.purge()
    True
    >>> n.exists()
    False
    >>> n.closest_parent()
    <Network: 8.8.0.0/16>

    :param cidr: CIDR for network
    '''

    def postinit(self, cidr=None):
        if not any([cidr, self.raw]):
            raise TypeError('Networks require a cidr')
        net = IPNetwork(cidr)

        ver = net.version
        self.network_address = str(net.network)
        self.prefix_length = int(net.prefixlen)
        self.is_host = ver == 4 and net.prefixlen == 32 or net.prefixlen == 128
        self.init_payload()

    @property
    def identifier(self):
        return '%s/%d' % (self['network_address'], self['prefix_length'])

    @property
    def resource_name(self):
        return 'networks'

    def init_payload(self):
        '''This will init the payload property'''
        if self.raw:
            self.payload = self.raw
            return

        self.payload = {
            'is_ip': self.is_host,
            'network_address': self.network_address,
            'prefix_length': self.prefix_length,
            'state': self.is_host and 'assigned' or 'allocated',
            'site_id': self._site_id,
            'attributes': self.attributes,
        }

    def closest_parent(self):
        '''Returns resource object of the closest parent network

        Empty dictionary if no parent network

        :returns: Parent resource
        :rtype: pynsot.models.Network or dict
        '''
        self.ensure_client()
        site = getattr(self.client.sites(self['site_id']), self.resource_name)
        cidr = '%s/%s' % (self['network_address'], self['prefix_length'])
        try:
            lookup = get_result(site(cidr).closest_parent.get())
            return Network(raw=lookup)
        except Exception as e:
            self.log_error(e)
            return {}

    def __len__(self):
        return self['prefix_length']


class Device(Resource):
    '''Device Resource

    Subclass of Resource.

    >>> dev = Device(hostname='router1-nyc', site_id=1)
    >>> dev.exists()
    False
    >>>
    >>> dev.ensure()
    True
    >>>
    >>> dev.existing_resource()
    {u'attributes': {}, u'hostname': u'router1-nyc', u'id': 1, u'site_id': 1}
    >>> dev.purge()
    True
    >>>
    >>> dev.exists()
    False

    :param hostname: Device hostname
    '''

    def postinit(self, hostname=None):
        if not any([hostname, self.raw]):
            raise TypeError('Devices require a hostname')
        self.hostname = hostname
        self.init_payload()

    @property
    def identifier(self):
        return self.hostname

    @property
    def resource_name(self):
        return 'devices'

    def init_payload(self):
        if self.raw:
            self.payload = self.raw
            return

        self.payload = {
            'hostname': self.hostname,
            'site_id': self._site_id,
            'attributes': self.attributes,
        }


class Interface(Resource):
    '''Interface Resource

    Subclass of Resource

    :param addresses: Addresses on interface
    :type addresses: list
    :param description: Interface description
    :param device: Required, device interface is on. TODO: broken as currently
        implemented but will soon reflect the following type
    :type device: pynsot.models.Device
    :param type: Interface type as described by SNMP IF-TYPE's
    :type type: int
    :param mac_address: MAC of interface
    :param name: Required, name of interface
    :param parent_id: ID of parent interface
    :type parent_id: int
    :param speed: Speed of interface
    :type speed: int
    '''

    def postinit(self, **kwargs):
        self.addresses = kwargs.get('addresses') or []
        self.description = kwargs.get('description') or ''
        self.device = kwargs.get('device') or 0
        self._original_device = kwargs.get('device') or None
        self.type = kwargs.get('type') or 6
        self.mac_address = kwargs.get('mac_address') or '00:00:00:00:00:00'
        self.name = kwargs.get('name') or None
        self.parent_id = kwargs.get('parent_id') or None
        self.speed = kwargs.get('speed') or 1000

        if not all([self.name, self.device]) or self.raw:
            raise TypeError('Interfaces require both a name and device!')

        self.attempt_device()
        self.init_payload()

    def attempt_device(self):
        '''Attempt to set ``device`` attribute to its ID if hostname was given

        If an ID was provided during init, this happens in init. If a hostname
        was provided, we need to take care of a couple things.

        1. Attempt to fetch ID for existing device by the hostname. If this
           works, use this ID

        2. Should #1 fail, set device id to 0 to signify this device doesn't
           exist yet, hoping this method will be called again when it's time to
           create. The thought here is if a user is instantiating lots of
           resources at the same time, there's a chance the device this relates
           to is going to be created before this one actually gets called upon.

           0 is used instead of a more descriptive message because should the
           device still not exist when executing this, at least a device
           doesn't exist error would be returned instead of expecting int not
           str.
        '''

        rerun = isinstance(self._original_device, str) and self.device == 0
        first_run = isinstance(self.device, str)
        # If equal to 0, means it had failed before
        if rerun or first_run:
            d = Device(
                client=self.client,
                site_id=self._site_id,
                hostname=self._original_device,
            )
            if d.exists():
                self.device = d.existing_resource()['id']
                return True
            else:
                self.device = 0
                return False

    @property
    def identifier(self):
        return '%s on %s' % (self.name, self.device)

    @property
    def resource_name(self):
        return 'interfaces'

    def init_payload(self):
        if self.raw:
            self.payload = self.raw
            return

        # TODO: This currently will only work on init and not later since
        # init_payload is only called once. This is left over from when it was
        # just payload
        #
        # attempt_device should instead set self.payload['device'] directly
        self.attempt_device()
        self.payload = {
            'addresses': self.addresses,
            'description': self.description,
            'device': self.device,
            'type': self.type,
            'mac_address': self.mac_address,
            'name': self.name,
            'parent_id': self.parent_id,
            'speed': self.speed,
            'attributes': self.attributes,
            'site_id': self._site_id,
        }
