Python API
==========

The Python API offers flexibility when you need it and works well for extending
applications to be NSoT-aware.

In the examples below, we're going to assume the following common pre-work done
in your code:

.. code-block:: python

   from pynsot.client import get_api_client

   c = get_api_client()

.. note:: The tables under each section reflect the ``networks`` resource

   Unless otherwise stated, everything applies to other resources as well.

What is Slumber?
----------------

You might notice when following along that the API clients are Slumber
instances. Slumber is a wrapper around the `requests` library to make REST much
more pleasant to use in Python. Each attribute of the client object represents
part of the HTTP path.

For the purpose of pynsot you should be in good hands for the rest of this
document, but for more information on Slumber, see the
`official Slumber documentation`_.

It might help to also refer to the `REST docs`_ for NSoT.

.. _official Slumber documentation: http://slumber.readthedocs.org/en/v0.6.0/tutorial.html

.. _REST docs: http://nsot.readthedocs.org/en/latest/api/rest.html

Fetching Resources
------------------


+---------------+----------------------------------------------+
| HTTP Method   | GET                                          |
+---------------+----------------------------------------------+
| HTTP Path     | ``GET /api/sites/1/networks/``               |
|               |                                              |
|               | ``GET /api/sites/1/networks/1/``             |
|               |                                              |
|               | ``GET /api/sites/1/networks/10.0.0.0/24/``   |
|               |                                              |
|               | ``GET /api/sites/1/networks/?limit=1``       |
+---------------+----------------------------------------------+
| Python Client | ``c.sites(1).networks.get()``                |
|               |                                              |
|               | ``c.sites(1).networks(1).get()``             |
|               |                                              |
|               | ``c.sites(1).networks('10.0.0.0/24').get()`` |
|               |                                              |
|               | ``c.sites(1).networks.get(limit=1)``         |
+---------------+----------------------------------------------+

The details and comparisons are shown above to demystify what the client does.
This is the most basic form of fetching one or many resources.

Any of these calls should return either a single dictionary or a list of
dictionaries.

In the fourth example, note the HTTP query parameter. ``limit`` is used to
restrict the number of results returned (pagination) and ``offset`` can be
provided to begin after ``n``. In the returned payload are the suggested
``next`` and ``previous`` page URLs.

Query parameters are used for filtering on resource properties except for by
attribute values. (Those are covered in another section)

.. note::

    "all" in the following context means all, regardless of site. Sites are
    normally used to separate conflicting sets of data so unless you intend to
    span sites, try to use ``c.sites(ID)`` for your normal clienting

.. code-block:: python

   all_nets = c.networks.get()
   all_nets_for_site1 = c.sites(1).networks.get()
   all_hosts = c.networks.get(prefix_length=32)

   all_resources = {}

   for resource_name in ['networks', 'devices', 'interfaces']:
       client = getattr(c, resource_name)
       all_resources[resource_name] = client.get()

Creating Resources
------------------

+---------------+-------------------------------------+
| HTTP Method   | POST                                |
+---------------+-------------------------------------+
| HTTP Path     | ``POST /api/sites/1/networks/``     |
+---------------+-------------------------------------+
| Python Client | ``c.sites(1).networks.post({...})`` |
+---------------+-------------------------------------+

To create a resource, you POST the payload to the server. Each resource has
different required fields and defaults for those that aren't. The easiest way
to reference this information is via the CLI help, browsing ``/api/``, or
try-except to catch the HTTP 400 and inspect ``e.response.json()``.

NSoT also has BULK operations. The only difference is that the payload is an
array of resources.

.. code-block:: python

   net = {'attributes': {}, 'network_address': '10.0.1.0', 'prefix_length': 24}
   c.sites(1).networks.post(net)
   # {u'attributes': {},
   # u'id': 6,
   # u'ip_version': u'4',
   # u'is_ip': False,
   # u'network_address': u'10.0.1.0',
   # u'parent_id': 1,
   # u'prefix_length': 24,
   # u'site_id': 1,
   # u'state': u'allocated'}

   try:
       net = {'network_address': '8.8.8.0', 'prefix_length': 24}
       c.sites(1).networks.post(net)
   except Exception as e:
       print(e.response.json())
       # {u'error': {u'code': 400,
       # u'message': {u'attributes': [u'This field is required.']}},
       # u'status': u'error'}


Updating Resources (Replace)
----------------------------


+---------------+---------------------------------------------------+
| HTTP Method   | PUT                                               |
+---------------+---------------------------------------------------+
| HTTP Path     | ``PUT /api/sites/1/networks/1/``                  |
|               |                                                   |
|               | ``PUT /api/sites/1/networks/10.0.0.0/24/``        |
+---------------+---------------------------------------------------+
| Python Client | ``c.sites(1).networks(1).put({...})``             |
|               |                                                   |
|               | ``c.sites(1).networks('10.0.0.0/24').put({...})`` |
+---------------+---------------------------------------------------+

In NSoT, a PUT/Replace action means to update properties of a resource while
resetting to default the unspecified properties. This is typically to replace
``attributes`` but applies to any non set-in-stone property such as
``parent_id``, ``id``, the resource identity keys (hostname, network, etc), and
others.

A successful call will return the new payload representing the upstream
resource.

Like Creating, PUT also supports BULK operations.

.. code-block:: python

   # Fetch example resource
   net = c.sites(1).networks('10.0.1.0/24').get()
   # {u'attributes': {u'desc': u'test'},
   #  u'id': 3,
   #  u'ip_version': u'4',
   #  u'is_ip': False,
   #  u'network_address': u'10.0.1.0',
   #  u'parent_id': 1,
   #  u'prefix_length': 24,
   #  u'site_id': 1,
   #  u'state': u'allocated'}

   net['attributes'] = {}
   c.sites(1).networks('10.0.1.0/24').put(net)
   # {u'attributes': {},
   #  u'id': 3,
   #  u'ip_version': u'4',
   #  u'is_ip': False,
   #  u'network_address': u'10.0.1.0',
   #  u'parent_id': 1,
   #  u'prefix_length': 24,
   #  u'site_id': 1,
   #  u'state': u'allocated'}


Updating Resources (Partial)
----------------------------


+---------------+-----------------------------------------------------+
| HTTP Method   | PATCH                                               |
+---------------+-----------------------------------------------------+
| HTTP Path     | ``PATCH /api/sites/1/networks/1/``                  |
|               |                                                     |
|               | ``PATCH /api/sites/1/networks/10.0.0.0/24/``        |
+---------------+-----------------------------------------------------+
| Python Client | ``c.sites(1).networks(1).patch({...})``             |
|               |                                                     |
|               | ``c.sites(1).networks('10.0.0.0/24').patch({...})`` |
+---------------+-----------------------------------------------------+

As opposed to PUT which can replace existing data, PATCH is "safer" in that
regard. If you don't provide some keys in your update, they will be untouched.

As with PUT and POST, a successful one should return the new payload.

Like Creating, PATCH also supports BULK operations.

.. code-block:: python

   net = c.sites(1).networks('10.0.1.0/24').get()
   # {u'attributes': {u'dc': u'sfo'},
   # u'id': 3,
   # u'ip_version': u'4',
   # u'is_ip': False,
   # u'network_address': u'10.0.1.0',
   # u'parent_id': 1,
   # u'prefix_length': 24,
   # u'site_id': 1,
   # u'state': u'allocated'}

   net.pop('attributes')
   c.sites(1).networks('10.0.1.0/24').patch(net)
   # {u'attributes': {u'dc': u'sfo'},
   #  u'id': 3,
   #  u'ip_version': u'4',
   #  u'is_ip': False,
   #  u'network_address': u'10.0.1.0',
   #  u'parent_id': 1,
   #  u'prefix_length': 24,
   #  u'site_id': 1,
   #  u'state': u'allocated'}

Deleting Resources
------------------

+---------------+-------------------------------------------------+
| HTTP Method   | DELETE                                          |
+---------------+-------------------------------------------------+
| HTTP Path     | ``DELETE /api/sites/1/networks/1/``             |
|               |                                                 |
|               | ``DELETE /api/sites/1/networks/10.0.0.0/24/``   |
+---------------+-------------------------------------------------+
| Python Client | ``c.sites(1).networks(1).delete()``             |
|               |                                                 |
|               | ``c.sites(1).networks('10.0.0.0/24').delete()`` |
+---------------+-------------------------------------------------+

This one should be straight forward and there is no payload to deal with. Will
return bool.


.. code-block:: python

   c.sites(1).networks('10.0.1.0/24').delete()
   # True

Querying by Attribute Values
----------------------------

+---------------+-------------------------------------------------------------+
| HTTP Method   | GET                                                         |
+---------------+-------------------------------------------------------------+
| HTTP Path     | ``GET /api/sites/1/networks/query/?query='set query here'`` |
+---------------+-------------------------------------------------------------+
| Python Client | ``c.sites(1).networks.query.get(query='set query here')``   |
+---------------+-------------------------------------------------------------+

Set queries are the way to filter based an attributes and their values. The
syntax is typical set query syntax and is lightly discussed in
:ref:`set_queries`.

The query itself is passed as a query param to the ``/query/`` endpoint and can
contain regular expressions by suffixing the attribute name, as shown below:

.. code-block:: python

    # Everything matching exactly desc == test
    c.sites(1).networks.query.get(query='desc=test')
    # [{u'attributes': {u'dc': u'sfo', u'desc': u'test'},
    #   u'id': 2,
    #   u'ip_version': u'4',
    #   u'is_ip': False,
    #   u'network_address': u'10.0.0.0',
    #   u'parent_id': 1,
    #   u'prefix_length': 24,
    #   u'site_id': 1,
    #   u'state': u'allocated'}]

    # Everything with desc matching regex test.*
    c.sites(1).networks.query.get(query='desc_regex=test.*')
    # [{u'attributes': {u'desc': u'testing'},
    #   u'id': 1,
    #   u'ip_version': u'4',
    #   u'is_ip': False,
    #   u'network_address': u'10.0.0.0',
    #   u'parent_id': None,
    #   u'prefix_length': 8,
    #   u'site_id': 1,
    #   u'state': u'allocated'},
    #  {u'attributes': {u'dc': u'sfo', u'desc': u'test'},
    #   u'id': 2,
    #   u'ip_version': u'4',
    #   u'is_ip': False,
    #   u'network_address': u'10.0.0.0',
    #   u'parent_id': 1,
    #   u'prefix_length': 24,
    #   u'site_id': 1,
    #   u'state': u'allocated'},
    #  {u'attributes': {u'dc': u'chi', u'desc': u'tester'},
    #   u'id': 4,
    #   u'ip_version': u'4',
    #   u'is_ip': False,
    #   u'network_address': u'10.0.2.0',
    #   u'parent_id': 1,
    #   u'prefix_length': 24,
    #   u'site_id': 1,
    #   u'state': u'allocated'}]

    # Everything NOT dc == chi
    c.sites(1).networks.query.get(query='-dc=chi')
    # [{u'attributes': {},
    #   u'id': 7,
    #   u'ip_version': u'4',
    #   u'is_ip': False,
    #   u'network_address': u'8.8.8.0',
    #   u'parent_id': None,
    #   u'prefix_length': 24,
    #   u'site_id': 1,
    #   u'state': u'allocated'},
    #  {u'attributes': {u'desc': u'testing'},
    #   u'id': 1,
    #   u'ip_version': u'4',
    #   u'is_ip': False,
    #   u'network_address': u'10.0.0.0',
    #   u'parent_id': None,
    #   u'prefix_length': 8,
    #   u'site_id': 1,
    #   u'state': u'allocated'},
    #  {u'attributes': {u'dc': u'sfo', u'desc': u'test'},
    #   u'id': 2,
    #   u'ip_version': u'4',
    #   u'is_ip': False,
    #   u'network_address': u'10.0.0.0',
    #   u'parent_id': 1,
    #   u'prefix_length': 24,
    #   u'site_id': 1,
    #   u'state': u'allocated'},
    #  {u'attributes': {u'dc': u'sfo'},
    #   u'id': 6,
    #   u'ip_version': u'4',
    #   u'is_ip': False,
    #   u'network_address': u'10.0.1.0',
    #   u'parent_id': 1,
    #   u'prefix_length': 24,
    #   u'site_id': 1,
    #   u'state': u'allocated'},
    #  {u'attributes': {},
    #   u'id': 5,
    #   u'ip_version': u'4',
    #   u'is_ip': True,
    #   u'network_address': u'10.0.2.1',
    #   u'parent_id': 4,
    #   u'prefix_length': 32,
    #   u'site_id': 1,
    #   u'state': u'allocated'}]

    # Everything dc == chi
    c.sites(1).networks.query.get(query='dc=chi')
    # [{u'attributes': {u'dc': u'chi', u'desc': u'tester'},
    #   u'id': 4,
    #   u'ip_version': u'4',
    #   u'is_ip': False,
    #   u'network_address': u'10.0.2.0',
    #   u'parent_id': 1,
    #   u'prefix_length': 24,
    #   u'site_id': 1,
    #   u'state': u'allocated'}]



API Abstraction Models
----------------------

These models were created to abstract most of the API away from the user if
they didn't want or need it. An instance can be created by providing minimal
info such as CIDR and desired attributes or it can take raw payload from the
API and turn it into a model instance.

You can read the docstring in the :mod:`pynsot.models` module or follow the
links below for usage examples. We think it's a pretty solid way to do most
basic interaction.

* :class:`pynsot.models.Network`
* :class:`pynsot.models.Device`
* :class:`pynsot.models.Interface`
