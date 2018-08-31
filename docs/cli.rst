############
Command-Line
############

Welcome to the NSoT command-line interface (CLI). This is where the party
starts!

Before you proceed, please make sure that you've created a ``.pynsotrc``
file as detailed in the :doc:`config` guide.

Data Model
==========

If you aren't already familiarized with the data model for NSoT, it might be
helpful to refer to the `NSoT Data Model
<http://nsot.readthedocs.io/en/latest/models.html>`_ guide.

Commands
========

Each object type is assigned a positional command argument:

.. code-block:: bash

    $ nsot --help
    Usage: nsot [OPTIONS] COMMAND [ARGS]...

      Network Source of Truth (NSoT) command-line utility.

      For detailed documentation, please visit https://nsot.readthedocs.io

    Options:
      -v, --verbose  Toggle verbosity.
      --version      Show the version and exit.
      -h, --help     Show this message and exit.

    Commands:
      attributes  Attribute objects.
      changes     Change events.
      circuits        Circuit objects.
      devices     Device objects.
      interfaces  Interface objects.
      protocol_types  Protocol Type objects.
      protocols       Protocol objects.
      networks    Network objects.
      sites       Site objects.
      values      Value objects.

Actions
=======

Every object type has four eligible actions representing creation, retrieval,
update, and deletion (CRUD):

* add
* list
* remove
* update

.. note::
    There are two exceptions: :ref:`working_with_changes` and
    :ref:`working_with_values`, which are immutable and can only be viewed.

For example, for ``nsot devices``:

.. code-block:: bash

    $ nsot devices -h
    Usage: nsot devices [OPTIONS] COMMAND [ARGS]...

      Device objects.

      A device represents various hardware components on your network such as
      routers, switches, console servers, PDUs, servers, etc.

      Devices also support arbitrary attributes similar to Networks.

    Options:
      -h, --help  Show this message and exit.

    Commands:
      add     Add a new Device.
      list    List existing Devices for a Site.
      remove  Remove a Device.
      update  Update a Device.

Getting Help
============

Every object type and action for each has help text that can be accessed
using the ``-h/--help`` option. It's quite good. Use it!

Verbosity
=========

The CLI utility tries to be as concise as possibly when telling you what it's
doing. Sometimes it may be useful to increase verbosity using the
``-v/--verbose`` flag.

For example, if you encounter an error and want to know more:

.. code-block:: bash

    $ nsot devices add --hostname ''
    [FAILURE] hostname:  This field may not be blank.

    $ nsot --verbose devices add --hostname ''
    [FAILURE] hostname:  This field may not be blank.
    400 BAD REQUEST trying to add device with args: bulk_add=None, attributes={}, hostname=

Required Options
================

When adding objects, certain fields will be required. The required options will
be designated as such with a ``[required]`` tag in the help text (for example
from ``nsot sites add --help``::

    -n, --name NAME         The name of the Site.  [required]

If a required option is not provided, ``nsot`` will complain::

    Error: Missing option "-n" / "--name".

Site ID
=======

For all object types other than Sites, the ``-s/--site-id`` option is required
to specify which Site you would like the object to be under. See
:ref:`config_ref` for setting a default site.

.. _resource_types:

Resource Types
==============

NSoT refers internally to any object that can have attributes as *Resource
Types* or just *Resources* for short. As of this writing this includes Device,
Network, Interfaces, and Protocols objects.

You will also see command-line arguments referencing *Resource Name* to
indicate the name of a Resource Type.

There are a number of features, settings, command-line flags and command-line
arguments that are common to all Resource Types as they relate to managing or
displaying attribute values.

This will be important to note later on in this documentation.

.. _natural_keys:

Natural Keys
============

A "natural key" is a field or set of fields which can uniquely identify an
object. Natural keys are intended to be used as a human-readable identifer to
improve user experience and simplify interaction with NSoT.

For the purpose of display all objects have a natural key for one or more
fields as follows:

* Sites: ``{name}``
* Attributes: ``{resource_name:name}``
* Devices: ``{hostname}``
* Networks: ``{cidr}``
* Interfaces: ``{device_hostname:name}``
* Circuits: ``{interface_a}_{interface_z}``

Updating or Removing Objects
============================

When updating or removing objects, you may specify their unique ID or (if
applicable) their natural key.

For objects that do not support update by natural key, unique IDs can be
obtained using the ``list`` action.

Currently the only :ref:`resource_types` to currently support update or removal
by natural key are:

* Devices: ``hostname``
* Networks: ``cidr``
* Interfaces: ``slug_name``
* Circuits: ``slug_name``

For example, this illustrates updating a Network object by natural key (cidr)
or by ID:

.. code-block:: bash

   $ nsot networks list
   +--------------------------------------------------------------------------------+
   | ID   CIDR (Key)      Is IP?   IP Ver.   Parent          State       Attributes |
   +--------------------------------------------------------------------------------+
   | 1    10.10.10.0/24   False    4         None            allocated              |
   | 5    10.10.10.1/32   True     4         10.10.10.0/24   assigned               |
   +--------------------------------------------------------------------------------+

   $ nsot networks update --cidr 10.10.10.1/32 -a desc="Changing this"
   [SUCCESS] updated network

   $ nsot networks update -i 5 -a desc="Changing this"
   [SUCCESS] updated network

Updating Attributes
-------------------

When modifying attributes on :ref:`resource_types`, you have three actions to
choose from:

* Add (``--add-attributes``). This is the default behavior that will add
  attributes if they don't exist, or update them if they do.

* Delete (``--delete-attributes``). This will cause attributes to be
  deleted. If combined with ``--multi`` the attribute will be deleted if either
  no value is provided, or if the attribute no longer contains a valid value.

* Replace (``--replace-attributes``). This will cause attributes to
  replaced. If combined with ``--multi`` and multiple attributes of the same
  name are provided, only the last value provided will be used.

Please note that this does not apply when updating Attribute resources
themselves. Attribute values attached to :ref:`resource_types` are considered
to be "instances" of Attributes.

Viewing Objects
===============

The ``list`` action for each object type supports ``-i/--id``, ``-l/--limit`` and
``-o/--offset`` options.

* The ``-i/--id`` option will retrieve a single object by the provided unique
  ID and will override any other list options.
* The ``-l/--limit`` option will limit the set of results to ``N`` resources.
* The ``-o/--offset`` option will skip the first ``N`` resources.

.. _set_queries:

Set Queries
-----------

All :ref:`resource_types` support a ``-q/--query`` option that is a
representation of set operations for matching attribute/value pairs.

The operations are evaluated from left-to-right, where the first character
indicates the set operation:

+ ``+`` indicates a set *union*
+ ``-`` indicates a set *difference*
+ no marker indicates a set *intersection*

For example:

+ ``-q "vendor=juniper"`` would return the set intersection of objects with
  ``vendor=juniper``.
+ ``-q "vendor=juniper -metro=iad"`` would return the set difference of all
  objects with ``vendor=juniper`` (that is all ``vendor=juniper`` where
  ``metro`` is not ``iad``).
+ ``-q "vendor=juniper +vendor=cisco`` would return the set union of all
  objects with ``vendor=juniper`` or ``vendor=cisco`` (that is all objects
  matching either).

The ordering of these operations is important. If you are not familiar with set
operations, please check out `Basic set theory concepts and notation
<http://en.wikipedia.org/wiki/Set_theory#Basic_concepts_and_notation>`_
(Wikipedia).

.. note::
   The default display format for set queries is the same as
   ``-N/--natural-key`` (see below) for non-set-query lookups.

.. important::
    When performing a set query for more than one operation, you must enclose
    it in quotations so that the space characters are properly passed to the
    argument parser.

For example:

.. code-block:: bash

   $ nsot devices list --query vendor=juniper
   iad-r1
   lax-r2

   $ nsot devices list --query vendor=juniper -metro=iad  # Needs quotes!
   Error: no such option: -m

   $ nsot devices list --query 'vendor=juniper -metro=iad'  # There we go!
   lax-r2

   $ nsot devices list --query 'vendor=juniper +vendor=cisco'
   chi-r1
   chi-r2
   iad-r1
   iad-r2
   lax-r2

Because set queries return newline-delimited results, they can be nice for
quickly feeding lists of objects to other utilities. For example, ``snmpwalk``:

.. code-block:: bash

    # For all top of rack switches, poll SNMP IF-MIB::ifDescr and store in files
    nsot devices list -q role=tor | xargs -I '{}' sh -c 'snmpwalk -v2c -c public "$1" .1.3.6.1.2.1.2.2.1.2 > "$1-ifDescr.txt"' -- '{}'

.. _output_modifiers:

Output Modifiers
----------------

The following modifying flags are available when viewing objects.

All Objects
~~~~~~~~~~~

The following flags apply to all objects.

* ``-N/--natural-key`` - Display list results by their uniquely identifying
  :ref:`natural key <natural_keys>`. 

.. code-block:: bash

    $ nsot sites list --natural-key
    Demo Site

Resource Types
~~~~~~~~~~~~~~

The following output modifiers apply to :ref:`resource_types` only.

* ``-g/--grep`` - Display list results in a grep-friendly format. This modifies
  the output in a way where the natural key is displayed first, and then each
  attribute/value pair (if any) is displayed one per line. Concrete
  field/values are also displayed for each resource.

.. note::
   Objects without any attributes will still be displayed, only with concrete
   fields listed in grep format.

.. code-block:: bash
   
    $ nsot devices list --attributes vendor=juniper --grep
    lax-r2 hw_type=router
    lax-r2 metro=lax
    lax-r2 owner=jathan
    lax-r2 vendor=juniper
    lax-r2 hostname=lax-r2
    lax-r2 id=311
    lax-r2 site_id=1
    iad-r1 hw_type=router
    iad-r1 metro=iad
    iad-r1 owner=jathan
    iad-r1 vendor=juniper
    lax-r1 hostname=lax-r1
    lax-r1 id=312
    lax-r1 site_id=1

    $ nsot devices list --attributes vendor=juniper --grep | grep metro
    lax-r2 metro=lax
    iad-r1 metro=iad

* ``-d/--delimited`` - When performing a set query using ``-q/--query``, this
  will display set query results separated by commas instead of newlines.

.. code-block:: bash

   $ nsot devices list --query vendor=juniper ---delimited
   iad-r1,lax-r2

Bulk Addition of Objects
========================

Attributes, Devices, and Networks may be created in bulk by using the
``-b/--bulk-add`` option and specifying a file path to a colon-delimited file.

The format of this file must adhere to the following format:

+ The first line of the file must be the field names.
+ All required fields must be present, however, the order of any of the fields
  does not matter.
+ Repeat: The fields may be in any order so long as the required fields are
  present! Missing fields will fallback to their defaults!
+ Attribute pairs must be commma-separated, and in format k=v and the
  attributes must exist!
+ For any fields that require Boolean values, the following applies:

  - You may specify ``True`` or ``False`` and they will be evaluated
  - If the value for a field is not set it will evaluate to ``False``
  - Any other value for a field will evaluate to ``True``

Attributes
----------

Sample file for ``nsot devices add --bulk-add /tmp/attributes``:

.. code-block:: csv

    name:resource_name:required:description:multi:display
    owner:Network:True:Network owner:True:True
    metro:Device:False:Device metro:False:True

Devices
-------

Sample file for ``nsot devices add --bulk-add /tmp/devices``:

.. code-block:: csv

    hostname:attributes
    device5:foo=bar,owner=team-networking
    device6:foo=bar,owner=team-networking

Networks
--------

Sample file for ``nsot networks add --bulk-add /tmp/networks``:

.. code-block:: csv:

    cidr:attributes
    10.20.30.0/24:foo=bar,owner=team-networking
    10.20.31.0/24:foo=bar,owner=team-networking

Interfaces
----------

Bulk addition of Interfaces via CLI is not supported at this time.


Protocols
---------

Bulk addition of Protocols via CLI is not supported at this time.

.. _working_with_objects:

Working with Objects
====================

This section walks through the basics of how to interact with each object and
action from the command-line.

.. _working_with_sites:

Sites
-----

Sites are the top-level object from which all other objects descend. In
other words, Sites contain Attributes, Devices, Networks, Interfaces, etc.
These examples illustrate having many Sites, but in practice you'll probably
only have one or two sites.

Adding a Site:

.. code-block:: bash

    $ nsot sites add --name Spam --description 'Spam Site'
    [SUCCESS] added site with args: name=Spam, description=Spam Site!

Listing all Sites:

.. code-block:: bash

    $ nsot sites list
    +--------------------------+
    | ID   Name    Description |
    +--------------------------+
    | 1    Foo     Foo Site    |
    | 2    Bar     Bar Site    |
    | 3    Baz     Baz Site    |
    | 4    Spam    Sheep Site  |
    | 5    Sheep   Sheep Site  |
    +--------------------------+

Listing a single Site:

.. code-block:: bash:

    $ nsot sites list --name Foo
    +-------------------------+
    | ID   Name   Description |
    +-------------------------+
    | 1    Foo    Foo Site    |
    +-------------------------+

Listing a few Sites:

.. code-block:: bash

    $ nsot sites list --limit 2
    +--------------------------+
    | ID   Name    Description |
    +--------------------------+
    | 1    Foo     Foo Site    |
    | 2    Bar     Bar Site    |
    +--------------------------+

Updating a Site:

.. code-block:: bash

    $ nsot sites update --id 2 --name Snickers
    [SUCCESS] updated site with args: description=None, name=Snickers!

    $ nsot sites list --name Snickers
    +-----------------------------+
    | ID   Name       Description |
    +-----------------------------+
    | 2    Snickers   Bar Site    |
    +-----------------------------+

Removing a Site:

.. code-block:: bash

    $ nsot sites remove --id 1
    [SUCCESS] removed site with args: id=1!

.. _working_with_attributes:

Attributes
----------

Attributes are flexible key/value pairs or tags you may use to assign arbitrary
data to objects.

.. note::
    Before you may assign Attributes to other resources, you must create the
    Attribute first!

Adding an Attribute:

.. code-block:: bash

    $ nsot attributes add --site-id 1 -n owner --r Device -d "Owner of a device." --required
    [SUCCESS] Added attribute!

Listing all Attributes:

.. code-block:: bash

    $ nsot attributes list --site-id 1
    +-----------------------------------------------------------------------------+
    | ID   Name    Resource   Required?   Display?   Multi?   Description         |
    +-----------------------------------------------------------------------------+
    | 3    owner   Device     True        False      False    Owner of a device.  |
    | 4    foo     Network    False       False      False    Foo for devices     |
    | 2    owner   Network    False       False      False    Owner of a network. |
    +-----------------------------------------------------------------------------+

You may also list Attributes by name:

.. code-block:: bash

    $ nsot attributes list --site-id 1 --name owner
    +-----------------------------------------------------------------------------+
    | ID   Name    Resource   Required?   Display?   Multi?   Description         |
    +-----------------------------------------------------------------------------+
    | 3    owner   Device     False       True       False    Owner of a device.  |
    | 2    owner   Network    False       False      False    Owner of a network. |
    +-----------------------------------------------------------------------------+

When listing a single Attribute by ID, you get more detail:

.. code-block:: bash

    $ nsot attributes list --site-id 1 --id 3
    +--------------------------------------------------------------------------------------+
    | Name    Resource   Required?   Display?   Multi?   Constraints         Description   |
    +--------------------------------------------------------------------------------------+
    | owner   Device     False       False      False    pattern=            Device owner. |
    |                                                    valid_values=                     |
    |                                                    allow_empty=False                 |
    +--------------------------------------------------------------------------------------+

Updating an Attribute:

.. code-block:: bash

    $ nsot attributes update --site-id 1 --id 3 --no-required
    [SUCCESS] Updated attribute!

    $ nsot attributes list --site-id 1 --id 3
    +----------------------------------------------------------------------------+
    | ID   Name    Resource   Required?   Display?   Multi?   Description        |
    +----------------------------------------------------------------------------+
    | 3    owner   Device     False       False      False    Owner of a device. |
    +----------------------------------------------------------------------------+

Attributes may also be uniquely identifed by ``name`` and ``resource_name`` in
lieu of using ``id``:

.. code-block:: bash

    $ nsot attributes update --site-id 1 --name owner --resource-name device --multi
    [SUCCESS] Updated attribute!

    $ nsot attributes list --site-id 1 --name owner --resource-name device
    +----------------------------------------------------------------------------+
    | ID   Name    Resource   Required?   Display?   Multi?   Description        |
    +----------------------------------------------------------------------------+
    | 3    owner   Device     False       False      True     Owner of a device. |
    +----------------------------------------------------------------------------+

Removing an Attribute:

.. code-block:: bash

    $ nsot attributes remove --site-id 1 --id 6
    [SUCCESS] Removed attribute with args: id=6!

.. _working_with_networks:

Networks
--------

A Network resource can represent an IP Network or an IP Address. Working with
networks is usually done with CIDR notation. Networks can have any number of
arbitrary Attributes.

Adding a Network:

.. code-block:: bash

    $ nsot networks add --site-id 1 --cidr 192.168.0.0/16 --attributes owner=jathan
    [SUCCESS] Added network!

Listing Networks:

.. code-block:: bash:

    $ nsot networks list --site-id 1
    +------------------------------------------------------------------------------------+
    | ID   CIDR (Key)       Is IP?   IP Ver.   Parent ID        State       Attributes   |
    +------------------------------------------------------------------------------------+
    | 1    192.168.0.0/16   False    4         None             allocated   owner=jathan |
    | 2    10.0.0.0/16      False    4         None             allocated   owner=jathan |
    | 3    172.16.0.0/12    False    4         None             allocated                |
    | 4    10.0.0.0/24      False    4         10.0.0.0/16      allocated                |
    | 5    10.1.0.0/24      False    4         10.0.0.0/16      allocated                |
    | 6    192.168.0.1/32   True     4         192.168.0.0/16   allocated                |
    +------------------------------------------------------------------------------------+

You may also optionally exclude IP addresses with ``--no-include-ips``:

.. code-block:: bash

    $ nsot networks list --side-id 1 --no-include-ips
    +---------------------------------------------------------------------------------+
    | ID   CIDR (Key)       Is IP?   IP Ver.   Parent ID     State       Attributes   |
    +---------------------------------------------------------------------------------+
    | 1    192.168.0.0/16   False    4         None          allocated   owner=jathan |
    | 2    10.0.0.0/16      False    4         None          allocated   owner=jathan |
    | 3    172.16.0.0/12    False    4         None          allocated                |
    | 4    10.0.0.0/24      False    4         10.0.0.0/16   allocated                |
    | 5    10.1.0.0/24      False    4         10.0.0.0/16   allocated                |
    +---------------------------------------------------------------------------------+

Or, you may show only IP adddresses by using ``--no-include-networks``:

.. code-block:: bash

    $ nsot networks list --site-id 1 --no-include-networks
    +------------------------------------------------------------------------------------+
    | ID   CIDR (Key)       Is IP?   IP Ver.   Parent ID        State       Attributes   |
    +------------------------------------------------------------------------------------+
    | 6    192.168.0.1/32   True     4         192.168.0.0/16   allocated                |
    +------------------------------------------------------------------------------------+

Performing a set query on Networks by attribute/value:

.. code-block:: bash

    $ nsot networks list --site-id 1 --query owner=jathan
    10.0.0.0/16
    192.168.0.0/16

You may also display the results comma-delimited:

.. code-block:: bash

    $ nsot networks list --site-id 1 --query owner=jathan --delimited
    10.0.0.0/16,192.168.0.0/16

Updating a Network (``-a/--attributes`` can be provide once for each Attribute):

.. code-block:: bash

    $ nsot networks update --site-id 1 --cidr 192.168.0.0/16 -a owner=jathan -a foo=bar
    [SUCCESS] Updated network!

    $ nsot networks list --site-id 1 --cidr 192.168.0.0/16
    +---------------------------------------------------------------------------+
    | ID   CIDR (Key)      Is IP?   IP Ver.   Parent   State       Attributes   |
    +---------------------------------------------------------------------------+
    | 1    192.168.0.0/16  False    4         None     allocated   owner=nobody |
    |                                                              foo=bar      |
    +---------------------------------------------------------------------------+

To delete attributes, reference each attribute by name and include the
``--delete-attributes`` flag (here we're deleting the ``foo`` attribute):

.. code-block:: bash

    $ nsot networks update --site-id 1 --cidr 192.168.0.0/16 -a foo --delete-attributes
    [SUCCESS] Updated network!

    $ nsot networks list --site-id 1 --cidr 192.168.0.0/16
    +---------------------------------------------------------------------------+
    | ID   CIDR (Key)      Is IP?   IP Ver.   Parent   State       Attributes   |
    +---------------------------------------------------------------------------+
    | 1    192.168.0.0/16  False    4         None     allocated   owner=nobody |
    +---------------------------------------------------------------------------+

Removing a Network:

.. code-block:: bash

    $ nsot networks remove --site-id 1 --id 2
    [SUCCESS] Removed network!

You may also remove a Network by its CIDR:

.. code-block:: bash

    $ nsot networks remove --site-id 1 --cidr 10.20.30.0/24
    [SUCCESS] Removed network!

The deletion of a network will only work if the network does not have any children. If it has
children, an error is raised. Notice the error if we try to delete ``0.0.0.0/0``:

.. code-block:: bash
    $ nsot networks list
    +-----------------------------------------------------------------------------------+
    | ID   CIDR (Key)        Is IP?   IP Ver.   Parent           State       Attributes |
    +-----------------------------------------------------------------------------------+
    | 1    185.45.19.0/24    False    4         0.0.0.0/0        allocated              |
    | 7    185.45.19.5/32    True     4         185.45.19.0/24   assigned               |
    | 8    185.45.19.6/32    True     4         185.45.19.0/24   assigned               |
    | 9    185.45.19.7/32    True     4         185.45.19.0/24   assigned               |
    | 10   185.45.19.10/32   True     4         185.45.19.0/24   assigned               |
    | 11   185.45.19.8/32    True     4         185.45.19.0/24   assigned               |
    | 17   0.0.0.0/0         False    4         None             allocated              |
    +-----------------------------------------------------------------------------------+v

   $ nsot networks remove -i 17
    [FAILURE] Cannot delete some instances of model 'Network' because they are referenced through a
    protected foreign key: 'Network.parent'

In the case where you want to delete the network that has children, take for example the situation
above where quad0 was mistakably added. You may forcefully delete the network using the
``force-delete`` flag:

.. code-block:: bash
    $ nsot networks remove -i 17 --force-delete
    [SUCCESS] Removed network!

Forceful delete does not work if the network being deleted does not have a parent and it's child
networks are leaf nodes. Notice the error if we try to delete ``185.45.19.0/24``:

.. code-block:: bash
    $ nsot networks list
    +-----------------------------------------------------------------------------------+
    | ID   CIDR (Key)        Is IP?   IP Ver.   Parent           State       Attributes |
    +-----------------------------------------------------------------------------------+
    | 1    185.45.19.0/24    False    4         None             allocated              |
    | 7    185.45.19.5/32    True     4         185.45.19.0/24   assigned               |
    | 8    185.45.19.6/32    True     4         185.45.19.0/24   assigned               |
    | 9    185.45.19.7/32    True     4         185.45.19.0/24   assigned               |
    | 10   185.45.19.10/32   True     4         185.45.19.0/24   assigned               |
    | 11   185.45.19.8/32    True     4         185.45.19.0/24   assigned               |
    +-----------------------------------------------------------------------------------+

    $ nsot networks remove -i 1 --force-delete
    [FAILURE] You cannot forcefully delete a network that does not have a parent, and whose children
    are leaf nodes.

Ancestors
~~~~~~~~~

Recursively get all parents of a network:

.. code-block:: bash

    $ nsot networks list -c 10.20.30.1/32 ancestors
    +----------------------------------------------------------------------------+
    | ID   CIDR (Key)     Is IP?   IP Ver.   Parent       State       Attributes |
    +----------------------------------------------------------------------------+
    | 1    10.0.0.0/8     False    4         None         allocated              |
    | 20   10.20.0.0/16   False    4         10.0.0.0/8   allocated              |
    | 15   10.20.30.0/24  False    4         10.0.0.0/8   allocated              |
    +----------------------------------------------------------------------------+

Assignments
~~~~~~~~~~~

Get interface assignments for a network:

.. code-block:: bash

    $ nsot networks list -c 10.20.30.1/32 assignments
    +---------------------------+
    | ID   Hostname   Interface |
    +---------------------------+
    | 2    foo-bar1   eth0      |
    +---------------------------+

Children
~~~~~~~~

Get immediate children of a network:

.. code-block:: bash

    $ nsot networks list -c 10.20.30.0/24 children
    +-------------------------------------------------------------------------------+
    | ID   CIDR (Key)       Is IP?   IP Ver.   Parent         State      Attributes |
    +-------------------------------------------------------------------------------+
    | 16   10.20.30.1/32    True     4         10.20.30.0/24  assigned              |
    | 17   10.20.30.3/32    True     4         10.20.30.0/24  allocated             |
    | 18   10.20.30.16/28   False    4         10.20.30.0/24  allocated             |
    | 19   10.20.30.104/32  True     4         10.20.30.0/24  allocated             |
    +-------------------------------------------------------------------------------+

Closest Parent
~~~~~~~~~~~~~~

Get the closest matching parent of a network, even if the network isn't found in the database:

.. code-block:: bash

    $ nsot networks list -c 10.101.103.100/30
    No network found matching args: include_ips=True, root_only=False, network_address=None, state=None, include_networks=True, limit=None, prefix_length=None, offset=None, ip_version=None, attributes=(), cidr=10.101.103.100/30, query=None, id=None!

    $ nsot networks list -c 10.101.103.100/30 closest_parent
    +----------------------------------------------------------------------------+
    | ID   CIDR (Key)     Is IP?   IP Ver.   Parent       State       Attributes |
    +----------------------------------------------------------------------------+
    | 1    10.0.0.0/8     False    4         None         allocated              |
    +----------------------------------------------------------------------------+

Descendants
~~~~~~~~~~~

Recursively get all children of a network:

.. code-block:: bash

    $ nsot networks list -c 10.20.0.0/16 descendants
    +------------------------------------------------------------------------------------+
    | ID   CIDR (Key)       Is IP?   IP Ver.   Parent         State      Attributes      |
    +------------------------------------------------------------------------------------+
    | 15   10.20.30.0/24    True     4         10.20.0.0/16   allocated                  |
    | 16   10.20.30.1/32    True     4         10.20.30.0/24  assigned                   |
    | 17   10.20.30.3/32    True     4         10.20.30.0/24  allocated                  |
    | 18   10.20.30.16/28   False    4         10.20.30.0/24  allocated                  |
    | 19   10.20.30.104/32  True     4         10.20.30.0/24  allocated                  |
    +------------------------------------------------------------------------------------+

Next Address
~~~~~~~~~~~~

Get next available addresses for a network:

.. code-block:: bash

    $ nsot networks list -c 10.20.30.0/24 next_address -n 3
    10.20.30.2/32
    10.20.30.4/32
    10.20.30.5/32

Next Network
~~~~~~~~~~~~

Get next available networks for a network:

.. code-block:: bash

    $ nsot networks list -c 10.20.30.0/24 next_network -p 28 -n 3
    10.20.30.0/28
    10.20.30.32/28
    10.20.30.48/28

Parent
~~~~~~

Get parent network of a network:

.. code-block:: bash

    $ nsot networks list -c 10.20.30.0/24 parent
    +----------------------------------------------------------------------------+
    | ID   CIDR (Key)     Is IP?   IP Ver.   Parent       State       Attributes |
    +----------------------------------------------------------------------------+
    | 20   10.20.0.0/16   False    4         10.0.0.0/8   allocated              |
    +----------------------------------------------------------------------------+

Reserved
~~~~~~~~

Get all reserved networks:

.. code-block:: bash

    $ nsot networks list reserved
    +-------------------------------------------------------------------------------+
    | ID   CIDR (Key)       Is IP?   IP Ver.   Parent         State      Attributes |
    +-------------------------------------------------------------------------------+
    | 10   10.10.12.0/24    False    4         10.10.0.0/16   reserved              |
    | 12   10.10.10.15/32   True     4         10.10.10.0/24  reserved              |
    +-------------------------------------------------------------------------------+

Root
~~~~

Get parent of all ancestors of a network:

.. code-block:: bash

    $ nsot networks list -c 10.20.30.3/32 root
    +----------------------------------------------------------------------------+
    | ID   CIDR (Key)     Is IP?   IP Ver.   Parent       State       Attributes |
    +----------------------------------------------------------------------------+
    | 1    10.0.0.0/8     False    4         None         allocated              |
    +----------------------------------------------------------------------------+

Siblings
~~~~~~~~

Get networks with same parent as a network:

.. code-block:: bash

    $ nsot networks list -c 10.20.30.3/32 siblings
    +------------------------------------------------------------------------------------+
    | ID   CIDR (Key)       Is IP?   IP Ver.   Parent         State      Attributes      |
    +------------------------------------------------------------------------------------+
    | 16   10.20.30.1/32    True     4         10.20.30.0/24  assigned                   |
    | 18   10.20.30.16/28   False    4         10.20.30.0/24  allocated                  |
    | 19   10.20.30.104/32  True     4         10.20.30.0/24  allocated                  |
    +------------------------------------------------------------------------------------+

You may also include the network itself:

.. code-block:: bash

    $ nsot networks list -c 10.20.30.3/32 siblings --include-self
    +---------------------------------------------------------------------------------+
    | ID   CIDR (Key)       Is IP?   IP Ver.   Parent          State       Attributes |
    +---------------------------------------------------------------------------------+
    | 16   10.20.30.1/32    True     4         10.20.30.0/24   assigned               |
    | 17   10.20.30.3/32    True     4         10.20.30.0/24   allocated              |
    | 18   10.20.30.16/28   False    4         10.20.30.0/24   allocated              |
    | 19   10.20.30.104/32  True     4         10.20.30.0/24   allocated              |
    +---------------------------------------------------------------------------------+

Subnets
~~~~~~~

Given Network ``192.168.0.0/16``, you may the view Networks it contains (aka
subnets):

.. code-block:: bash

    $ nsot networks list --site-id 1 --cidr 192.168.0.0/16 subnets
    +---------------------------------------------------------------------------------+
    | ID   CIDR (Key)      Is IP?   IP Ver.   Parent           State       Attributes |
    +---------------------------------------------------------------------------------+
    | 6    192.168.0.0/24  False    4         192.168.0.0/16   allocated              |
    | 7    192.168.0.0/25  False    4         192.168.0.0/24   allocated              |
    +---------------------------------------------------------------------------------+

Supernets
~~~~~~~~~

Given a Network ``192.168.0.0/24``, you may view the Networks containing it
(aka supernets):

.. code-block:: bash

    $ nsot networks list --site-id 1 --cidr 192.168.0.0/16
    +---------------------------------------------------------------------------------+
    | ID   CIDR (Key)      Is IP?   IP Ver.   Parent           State       Attributes |
    +---------------------------------------------------------------------------------+
    | 6    192.168.0.0/24  False    4         192.168.0.0/16   allocated              |
    +---------------------------------------------------------------------------------+

You may view the networks that contain that Network (aka supernets):

.. code-block:: bash

    $ nsot networks list --site-id 1 --id 192.168.0.0/24 supernets
    +------------------------------------------------------------------------+
    | ID   CIDR (Key)      Is IP?   IP Ver.   Parent   State      Attributes |
    +------------------------------------------------------------------------+
    | 6    192.168.0.0/16  False    4         None     allocated             |
    +------------------------------------------------------------------------+

.. _working_with_devices:

Devices
-------

A Device represents various hardware components on your network such as
routers, switches, console servers, PDUs, servers, etc.

Devices also support arbitrary attributes similar to Networks.

Adding a Device:

.. code-block:: bash

    $ nsot devices add --site-id 1 --hostname foo-bar1 --attributes owner=neteng
    [SUCCESS] Added device!

Listing Devices:

.. code-block:: bash

    $ nsot devices list --site-id 1
    +------------------------------+
    | ID   Hostname   Attributes   |
    +------------------------------+
    | 1    foo-bar1   owner=jathan |
    | 2    foo-bar2   owner=neteng |
    | 3    bar-baz1   owner=jathan |
    | 4    bar-baz2   owner=neteng |
    +------------------------------+

Performing a set query on Device by attribute/value:

.. code-block:: bash

    $ nsot devices list --site-id 1 --query owner=neteng
    bar-baz2
    foo-bar2

You may also display the results comma-delimited:

.. code-block:: bash

    $ nsot devices list --site-id 1 --query owner=neteng --delimited
    bar-baz2,foo-bar2

Updating a Device:

.. code-block:: bash

    $ nsot devices update --id 1 --hostname potato
    [SUCCESS] Updated device with args: attributes={}, hostname=potato!

    $ ./nsot devices list --site-id 1 --id 1
    +----------------------------+
    | ID   Hostname   Attributes |
    +----------------------------+
    | 1    potato                |
    +----------------------------+

To delete attributes, reference each attribute by name and include the
``--delete-attributes`` flag:

.. code-block:: bash

    $ nsot devices update --site-id 1 --id 2 -a owner --delete-attributes

    $ nsot devices list --site-id 1 --id 2
    +------------------------------+
    | ID   Hostname   Attributes   |
    +------------------------------+
    | 2    foo-bar2                |
    +------------------------------+

Removing a Device:

.. code-block:: bash

    $ nsot devices remove --site-id 1 --id 1
    [SUCCESS] Removed device!

You may also remove a Device by its hostname:

.. code-block:: bash

    $ nsot devices remove --site-id 1 --hostname delete-me
    [SUCCESS] Removed device!

Interfaces
~~~~~~~~~~

.. note::
    If you don't have any interfaces yet, that's ok. Skip to the next section
    and refer back here when you do.

Device objects also allow you to display their interfaces using the
``interfaces`` sub-command:

.. code-block:: bash

    $ nsot devices list --hostname foo-bar1 interfaces
    +-------------------------------------------------------------+
    | ID   Name (Key)      Parent   MAC    Addresses   Attributes |
    +-------------------------------------------------------------+
    | 1    foo-bar1:eth0   None     None                          |
    | 2    foo-bar1:eth1   None     None                          |
    +-------------------------------------------------------------+

.. _working_with_interfaces:

Interfaces
----------

An Interface represents a network interface or port on a Device. Interfaces
may only be created by "attaching" them to a Device object, just like in real
life.

Interfaces, like all other :ref:`resource_types`, support arbitrary attributes.

For these examples, we're going to assume we've got a Device object with
hostname ``foo-bar1`` with id of ``1``.

Adding an Interface:

.. code-block:: bash

    $ nsot interfaces add --device foo-bar1 --name eth0 
    [SUCCESS] Added interface!

Let's add another Interface:

.. code-block:: bash

    $ nsot interfaces add --device foo-bar1 --name eth1
    [SUCCESS] Added interface!

Listing all Interfaces:

.. code-block:: bash

    $ nsot interfaces list
    +-------------------------------------------------------------+
    | ID   Name (Key)      Parent   MAC    Addresses   Attributes |
    +-------------------------------------------------------------+
    | 1    foo-bar1:eth0   None     None                          |
    | 2    foo-bar1:eth1   None     None                          |
    +-------------------------------------------------------------+

Listing a single Interface shows more detail:

.. code-block:: bash

    $ nsot interfaces list --name eth0
    +----------------------------------------------------------------------------+
    | ID   Name (Key)      Parent   MAC    Addresses   Speed   Type   Attributes |
    +----------------------------------------------------------------------------+
    | 1    foo-bar1:eth0   None     None               1000    6                 |
    +----------------------------------------------------------------------------+

But what if you've got more than one interface named ``eth0``? You can filter
interfaces by ``-D/--device``, which when listing can either be ID or hostname
of the device:

.. code-block:: bash

    $ nsot interfaces list --device foo-bar1 -n eth0
    +----------------------------------------------------------------------------+
    | ID   Name (Key)      Parent   MAC    Addresses   Speed   Type   Attributes |
    +----------------------------------------------------------------------------+
    | 1    foo-bar1:eth0   None     None               1000    6                 |
    +----------------------------------------------------------------------------+

You may also specify a parent Interface on the same device:

.. code-block:: bash

    $ nsot interfaces add --device foo-bar1 --name eth0.0 --parent-id foo-bar1:eth0
    [SUCCESS] Added interface!

    $ nsot interfaces list --id foo-bar1:eth0.0 
    +-------------------------------------------------------------------------------------+
    | ID   Name (Key)        Parent          MAC    Addresses   Speed   Type   Attributes |
    +-------------------------------------------------------------------------------------+
    | 26   foo-bar1:eth0.0   foo-bar1:eth0   None               1000    6                 |
    +-------------------------------------------------------------------------------------+

Interfaces also support attributes:

.. code-block:: bash

    $ nsot attributes add --resource-name interface --name vlan
    [SUCCESS] Added attribute!

    $ nsot interfaces update --id foo-bar1:eth0 -a vlan=100
    [SUCCESS] Updated interface!

    $ nsot interfaces update --id foo-bar1:eth1 -a vlan=100
    [SUCCESS] Updated interface!

    $ nsot interfaces list --id foo-bar1:eth0
    +----------------------------------------------------------------------------+
    | ID   Name (Key)      Parent   MAC    Addresses   Speed   Type   Attributes |
    +----------------------------------------------------------------------------+
    | 1    foo-bar1:eth0   None     None               1000    6      vlan=100   |
    +----------------------------------------------------------------------------+

Performing a set query on Interfaces by attribute/value displays by natural key
``device_hostname:name``):

.. code-block:: bash

    $ nsot interfaces list --query vlan=100
    foo-bar1:eth0
    foo-bar1:eth1

You may also display the results comma-delimited:

.. code-block:: bash

    $ nsot interfaces list --query vlan=100 --delimited
    foo-bar1:eth0,foo-bar1:eth1

You may also specify the ``type`` (ethernet, etc... more on this later),
``speed`` (in Mbps), and ``mac_address``:

.. code-block:: bash

    $ nsot interfaces update --id foo-bar1:eth1 --speed 10000 --type 161 --mac-address 6C:40:08:A5:96:86
    [SUCCESS] Updated interface!

    $ nsot interfaces list --id foo-bar1:eth1
    +-----------------------------------------------------------------------------------------+
    | ID   Name (Key)      Parent   MAC                 Addresses   Speed   Type   Attributes |
    +-----------------------------------------------------------------------------------------+
    | 2    foo-bar1:eth1   None     6C:40:08:A5:96:86               10000   161    vlan=100   |
    +-----------------------------------------------------------------------------------------+

You may also assign IP addresses to Interfaces. These are represented by an
``assignment`` relationship to a Network object that contains a host address
(``/32`` for IPv4 or ``/128`` for IPv6). When assigning an address to an
Interface, if a record does not already exist, one is created with
``state=assigned``. If one does exist, its state is updated:

.. code-block:: bash

    $ nsot interfaces update --id foo-bar1:eth0 --addresses 10.10.10.1/32
    [SUCCESS] Updated interface!

    $ nsot interfaces list --id foo-bar1:eth0
    +--------------------------------------------------------------------------------+
    | ID   Name (Key)      Parent   MAC    Addresses       Speed   Type   Attributes |
    +--------------------------------------------------------------------------------+
    | 1    foo-bar1:eth0   None     None   10.10.10.1/32   1000    6      vlan=100   |
    +--------------------------------------------------------------------------------+

Just like in real life, it is an error to assign an IP address to already
assigned to another interface on the same Device:

.. code-block:: bash

    $ nsot interfaces update --id foo-bar1:eth1 --addresses 10.10.10.1/32
    [FAILURE] address: Address already assigned to this Device.

Removing an Interface:

.. code-block:: bash

    $ nsot interfaces remove --id 2
    [SUCCESS] Removed interface!

Interfaces can also be removed by natural key

.. code-block:: bash

    $ nsot interfaces remove --id foo-bar1:eth1
    [SUCCESS] Removed interface!

Addresseses
~~~~~~~~~~~

Given an Interface, you may display the associated Network addresses:

.. code-block:: bash

    $ nsot interfaces list --id foo-bar1:eth0 addresses
    +-------------------------------------------------------------------------------+
    | ID   CIDR (Key)      Is IP?   IP Ver.   Parent          State      Attributes |
    +-------------------------------------------------------------------------------+
    | 5    10.10.10.1/32   True     4         10.10.10.0/24   assigned              |
    +-------------------------------------------------------------------------------+

Ancestors
~~~~~~~~~

Recursively get all parents of an Interface.

.. code-block:: bash

    $ nsot interfaces list -i foo-bar1:vlan100 ancestors
    +--------------------------------------------------------------------------+
    | ID   Name (Key)        Parent          MAC    Addresses       Attributes |
    +--------------------------------------------------------------------------+
    | 24   foo-bar1:eth0     None            None   10.10.10.1/32   vlan=100   |
    | 26   foo-bar1:eth0.0   foo-bar1:eth0   None                              |
    +--------------------------------------------------------------------------+

Assignments
~~~~~~~~~~~

Given an Interface, you may display the underlying assignment objects that
represent the relationship between ``Interface <=> Network``:

.. code-block:: bash

    $ nsot interfaces list --id 1 assignments
    +----------------------------------------------------------------------+
    | ID   Device     Device ID   Address         Interface   Interface ID |
    +----------------------------------------------------------------------+
    | 1    foo-bar1   1           10.10.10.1/32   eth0        1            |
    +----------------------------------------------------------------------+

Children
~~~~~~~~

Get immediate children of an Interface.

.. code-block:: bash

    $ nsot interfaces list -i foo-bar1:eth0 children
    +----------------------------------------------------------------------+
    | ID   Name (Key)        Parent          MAC    Addresses   Attributes |
    +----------------------------------------------------------------------+
    | 26   foo-bar1:eth0.0   foo-bar1:eth0   None                          |
    +----------------------------------------------------------------------+

Descendants
~~~~~~~~~~~

Recursively get all children of an Interface.

.. code-block:: bash

    $ nsot interfaces list -i foo-bar1:eth0 descendants
    +-------------------------------------------------------------------------+
    | ID   Name (Key)         Parent            MAC    Addresses   Attributes |
    +-------------------------------------------------------------------------+
    | 26   foo-bar1:eth0.0    foo-bar1:eth0     None                          |
    | 28   foo-bar1:vlan100   foo-bar1:eth0.0   None                          |
    +-------------------------------------------------------------------------+

Networks
~~~~~~~~

Given an Interface, you may display the containing networks for any addresses
assigned to the interface:

.. code-block:: bash

    $ nsot interfaces list --id foo-bar1:eth0 networks
    +-------------------------------------------------------------------------+
    | ID   CIDR (Key)      Is IP?   IP Ver.   Parent   State       Attributes |
    +-------------------------------------------------------------------------+
    | 4    10.10.10.0/24   False    4         None     allocated              |
    +-------------------------------------------------------------------------+

Parent
~~~~~~

Get the parent Interface of an Interface.

.. code-block:: bash

    $ nsot interfaces list -i foo-bar1:eth0.0 parent
    +--------------------------------------------------------------------------------+
    | ID   Name (Key)      Parent   MAC    Addresses       Speed   Type   Attributes |
    +--------------------------------------------------------------------------------+
    | 24   foo-bar1:eth0   None     None   10.10.10.1/32   1000    6      vlan=100   |
    +--------------------------------------------------------------------------------+

Root
~~~~

Get parent of all ancestors of an Interface.

.. code-block:: bash

    $ nsot interfaces list -i foo-bar1:vlan100 root
    +--------------------------------------------------------------------------------+
    | ID   Name (Key)      Parent   MAC    Addresses       Speed   Type   Attributes |
    +--------------------------------------------------------------------------------+
    | 24   foo-bar1:eth0   None     None   10.10.10.1/32   1000    6      vlan=100   |
    +--------------------------------------------------------------------------------+


Siblings
~~~~~~~~

Get Interfaces with the same parent and Device as an Interface.

To illustrate we'll add another Interface, setting its parent to
``foo-bar1:eth0.0`` (the same as parent as ``fooo-bar1:vlan100`` in the
previous examples):

.. code-block:: bash

    $ nsot interfaces add -D foo-bar1 -n vlan200 -p foo-bar1:eth0.0
    [SUCCESS] Added interface!

    $ nsot interfaces list -i foo-bar1:vlan200 siblings
    +----------------------------------------------------------------------------------------+
    | ID   Name (Key)         Parent            MAC    Addresses   Speed   Type   Attributes |
    +----------------------------------------------------------------------------------------+
    | 28   foo-bar1:vlan100   foo-bar1:eth0.0   None               1000    6                 |
    +----------------------------------------------------------------------------------------+

And ``foo-bar:vlan100`` shows ``foo-bar1:vlan200`` as its sibling:

.. code-block:: bash

    $ nsot interfaces list -i foo-bar1:vlan100 siblings
    +----------------------------------------------------------------------------------------+
    | ID   Name (Key)         Parent            MAC    Addresses   Speed   Type   Attributes |
    +----------------------------------------------------------------------------------------+
    | 29   foo-bar1:vlan200   foo-bar1:eth0.0   None               1000    6                 |
    +----------------------------------------------------------------------------------------+

Circuits
--------

A Circuit represents a physical or logical circuit between two network
interfaces, such as a backbone interconnect or external peering.

Circuits are created by binding local (A-side) and remote (Z-side) Interface
objects. Interfaces may only be bound to a single Circuit at a time. The Z-side
Interface is optional, such as if you want to model a circuit for which you do
not own the remote side.

Circuits, like all other :ref:`resource_types`, support arbitrary attributes.

For these examples we'll start with two Devices each with Interfaces with addresses assigned to them. 

* The local (A-side) Interface will be ``lax-r1:ae0``
* The remote (Z-side) Interface will be ``nyc-r1:ae0``

Adding a Circuit is done by specifying the A- and Z-side Interfaces:

.. code-block:: bash

    $ nsot circuits add -A lax-r1:ae0 -Z nyc-r1:ae0
    [SUCCESS] Added circuit!

Listing all Circuits, observing that the circuit name was automatically generated from the natural key of the Interfaces bound to the circuit:

.. code-block:: bash

    $ nsot circuits list
    +-------------------------------------------------------------------+
    | ID   Name (Key)              Endpoint A   Endpoint Z   Attributes |
    +-------------------------------------------------------------------+
    | 4    lax-r1:ae0_nyc-r1:ae0   lax-r1:ae0   nyc-r1:ae0              |
    +-------------------------------------------------------------------+

Listing a single Circuit by name:

.. code-block:: bash

    $ nsot circuits list -n lax-r1:ae0_nyc-r1:ae0
    +-------------------------------------------------------------------+
    | ID   Name (Key)              Endpoint A   Endpoint Z   Attributes |
    +-------------------------------------------------------------------+
    | 4    lax-r1:ae0_nyc-r1:ae0   lax-r1:ae0   nyc-r1:ae0              |
    +-------------------------------------------------------------------+

Circuits also support attributes:

.. code-block:: bash

    $ nsot attributes add --resource-name circuit --name scope
    [SUCCESS] Added attribute!

    $ nsot circuits update -i lax-r1:ae0_nyc-r1:ae0 -a scope=metro
    [SUCCESS] Updated circuit!

    $ nsot circuits list -n lax-r1:ae0_nyc-r1:ae0
    +--------------------------------------------------------------------+
    | ID   Name (Key)              Endpoint A   Endpoint Z   Attributes  |
    +--------------------------------------------------------------------+
    | 4    lax-r1:ae0_nyc-r1:ae0   lax-r1:ae0   nyc-r1:ae0   scope=metro |
    +--------------------------------------------------------------------+

Performing a set query on Circuits by atrribute/value displays by natural key:

.. code-block:: bash

    $ nsot circuits list -q scope=metro
    lax-r1:ae0_nyc-r1:ae0

Circuits can be updated by ID:

.. code-block:: bash

    $ nsot circuits update -i 4 -a scope=region
    [SUCCESS] Updated circuit!

    $ nsot circuits list -i 4
    +---------------------------------------------------------------------+
    | ID   Name (Key)              Endpoint A   Endpoint Z   Attributes   |
    +---------------------------------------------------------------------+
    | 4    lax-r1:ae0_nyc-r1:ae0   lax-r1:ae0   nyc-r1:ae0   scope=region |
    +---------------------------------------------------------------------+

Circuits can also be updated by natural key:

.. code-block:: bash

    $ nsot circuits update -i lax-r1:ae0_nyc-r1:ae0 --delete-attributes -a scope
    [SUCCESS] Updated circuit!

    $ nsot circuits list -i lax-r1:ae0_nyc-r1:ae0
    +-------------------------------------------------------------------+
    | ID   Name (Key)              Endpoint A   Endpoint Z   Attributes |
    +-------------------------------------------------------------------+
    | 4    lax-r1:ae0_nyc-r1:ae0   lax-r1:ae0   nyc-r1:ae0              |
    +-------------------------------------------------------------------+

Removing a Circuit can be done by ID:

.. code-block:: bash

    $ nsot circuits remove -i 4
    [SUCCESS] Removed circuit!

Circuits can also be removed by natural key:

.. code-block:: bash

    $ nsot circuits remove -i lax-r1:ae0_nyc-r1:ae0
    [SUCCESS] Removed circuit!

Addresses
~~~~~~~~~

Returns the addresses assigned to the member Interfaces of the Circuit, if any.

.. code-block:: bash

    $ nsot circuits list -i lax-r1:ae0_nyc-r1:ae0 addresses
    +---------------------------------------------------------------------------------+
    | ID   CIDR (Key)       Is IP?   IP Ver.   Parent           State      Attributes |
    +---------------------------------------------------------------------------------+
    | 7    192.168.0.1/32   True     4         192.168.0.0/16   assigned              |
    | 8    192.168.0.2/32   True     4         192.168.0.0/16   assigned              |
    +---------------------------------------------------------------------------------+

Devices
~~~~~~~

Returns the Devices to which the member Interfaces are attached.

.. code-block:: bash

    $ nsot circuits list -i lax-r1:ae0_nyc-r1:ae0 devices
    +----------------------------------+
    | ID   Hostname (Key)   Attributes |
    +----------------------------------+
    | 6    lax-r1                      |
    | 7    nyc-r1                      |
    +----------------------------------+

Interfaces
~~~~~~~~~~

Returns the Interface objects bound to the circuit ordered from A to Z (local
to remote).

.. code-block:: bash

    $ nsot circuits list -i lax-r1:ae0_nyc-r1:ae0 interfaces
    +---------------------------------------------------------------+
    | ID   Name (Key)   Parent   MAC    Addresses        Attributes |
    +---------------------------------------------------------------+
    | 30   lax-r1:ae0   None     None   192.168.0.1/32              |
    | 31   nyc-r1:ae0   None     None   192.168.0.2/32              |
    +---------------------------------------------------------------+

.. _working_with_values:

Protocol Types
--------------

A Protocol Type resource represents a network protocol type (e.g. bgp, is-is, ospf, etc.)

Protocol Types can have any number of required attributes.

Adding a Protocol Type is done by specifying the name:

.. code-block:: bash

    $ nsot protocol_types add --name bgp
    [SUCCESS] Added protocol_type!

Let's add another Protocol Type:

.. code-block:: bash

    $ nsot protocol_types add --name ospf
    [SUCCESS] Added protocol_type!

Listing all Protocol Types:

.. code-block:: bash

    $ nsot protocol_types list
    +-----------------------------------------------+
    | ID   Name   Description   Required Attributes |
    +-----------------------------------------------+
    | 1    bgp                                      |
    | 2    ospf                                     |
    +-----------------------------------------------+

Protocol Types also allow you to add required attributes for future protocols of this type. This is done by the name of the attribute:

.. code-block:: bash

    $ nsot protocol_types add --name tcp --required-attribute foo
    [SUCCESS] Added protocol_type!

    $ nsot protocol_types list
    +-----------------------------------------------+
    | ID   Name   Description   Required Attributes |
    +-----------------------------------------------+
    | 1    bgp                                      |
    | 2    ospf                                     |
    | 3    tcp                  foo                 |
    +-----------------------------------------------+

Note that this only works if the attribute has already been created for the Protocol resource. Notice what happens if we try to add the ``bar`` attribute to the Protocol Type:

.. code-block:: bash

    $ nsot protocol_types add --name ip --required-attribute bar
    [FAILURE] required_attributes:  Object with name=bar does not exist.

    $ nsot attributes add --resource-name protocol --name bar
    [SUCCESS] Added attribute!

Now that ``bar`` has been created, it can be added as a required-attribute on the Protocol Type:

.. code-block:: bash

    $ nsot protocol_types add --name ip -required-attribute bar
    [SUCCESS] Added protocol_type!

You can also update the name of your protocol_type:

.. code-block:: bash

    $ nsot protocol_types update --id 1 --name test
    [SUCCESS] Updated protocol_type!

    $ nsot protocol_types list
    +-----------------------------------------------+
    | ID   Name   Description   Required Attributes |
    +-----------------------------------------------+
    | 1    test                                     |
    | 2    ospf                                     |
    | 3    tcp                  foo                 |
    | 4    ip                   bar                 |
    +-----------------------------------------------+

You can add required-attributes to a protocol_type that has already been created:

.. code-block:: bash

    $ nsot protocol_types update --id 1 --required-attribute baz
    [SUCCESS] Updated protocol_type!

    $ nsot protocol_types list
    +-----------------------------------------------+
    | ID   Name   Description   Required Attributes |
    +-----------------------------------------------+
    | 1    test                 baz                 |
    | 2    ospf                                     |
    | 3    tcp                  foo                 |
    | 4    ip                   bar                 |
    +-----------------------------------------------+

Removing a Protocol Type:

.. code-block:: bash

    $ nsot protocol_types remove --id 1
    [SUCCESS] Removed protocol_type!


Protocols
---------

A Protocol represents a network routing protocol.

Protocols, like all other :ref:`resource_types`, support arbitrary attributes.

Adding a Protocol is done by specifying the protocol_type (-t/--type), device id or natural key (-D/--device), and interface id or natural key (-I/--interface). You can also optionally provide a description (-e/--description) for the protocol, as shown below. Since there are many flags to pass infor the `add` operation, we will use the shorter flag option.

.. code-block:: bash

    $ nsot protocols add -t ospf -D foo-bar01 -I foo-bar01:etho0 -e 'my new proto'
    [SUCCESS] Added protocol!

It's important to note that you must create the :ref:`protocol_type` before you can add a protocol of that type. For example, see what happens if I try to create a new protocol of type `bgp` without having added this protocol_type first:

.. code-block:: bash

    $ nsot protocols add -t bgp -D foo-bar01 -I foo-bar01:etho0 -e 'this wont work'
    [FAILURE] type:  Object with name=bgp does not exist.

If we add the Protocol Type and rerun the above command, it will allow a protocol to be created:

.. code-block:: bash

    $ nsot protocol_types add -n bgp
    [SUCCESS] Added protocol_type!

    $ nsot protocols add -t bgp -D foo-bar01 -I foo-bar01:etho0 -e 'this will work'
    [SUCCESS] Added protocol!

We can see both protocols by running list:

.. code-block:: bash

    $ nsot protocols list
    +----------------------------------------------------------------+
    | ID   Device      Type   Interface         Circuit   Attributes |
    +----------------------------------------------------------------+
    | 1    foo-bar01   ospf   foo-bar01:etho0   None                 |
    | 2    foo-bar01   bgp    foo-bar01:etho0   None                 |
    +----------------------------------------------------------------+

If, however, the Protocol Type has a ``required-attribute``, you will need to provide this when adding a protocol of that type. For example:

.. code-block:: bash

    $ nsot protocol_types list
    +-----------------------------------------------+
    | ID   Name   Description   Required Attributes |
    +-----------------------------------------------+
    | 2    ospf                                     |
    | 3    tcp                  my_attr             |
    | 4    ip                   bar                 |
    +-----------------------------------------------+

Notice that the protocol_type ``tcp`` has a required attribute named ``my_attr``. This means this if you create a protocol of this type, you will need to provide a key, value pair (format: key=value), where key is the protocol_type's required attribute name. See the example below:

.. code-block:: bash

    $ nsot protocols add -t tcp -D foo-bar01 -I foo-bar01:etho0 -e 'this wont work'
    [FAILURE] attributes: Missing required attributes: my_attr

    $ nsot protocols add -t tcp -D foo-bar01 -I foo-bar01:etho0 -a my_attr=test -e 'this will work'
    [SUCCESS] Added protocol!

Listing a single Protocol by type:

.. code-block:: bash

    $ nsot protocols list -t bgp
    +----------------------------------------------------------------+
    | ID   Device      Type   Interface         Circuit   Attributes |
    +----------------------------------------------------------------+
    | 2    foo-bar01   bgp    foo-bar01:etho0   None                 |
    +----------------------------------------------------------------+

Protocols also support attributes:

.. code-block:: bash

    $ nsot attributes add --resource-name protocol --name foo
    [SUCCESS] Added attribute!

    $ nsot protocols update --id 1 --attributes foo=test_attribute
    [SUCCESS] Updated protocol!

    $ nsot protocols list -i 1
    +------------------------------------------------------------------------------------------------------------+
    | ID   Device      Type   Interface         Circuit   Auth_String   Description    Site   Attributes         |
    +------------------------------------------------------------------------------------------------------------+
    | 1    foo-bar01   ospf   foo-bar01:etho0   None                    my new proto   1      foo=test_attribute |
    +------------------------------------------------------------------------------------------------------------+

Performing a set query on Protocols by attribute/value displays by natural key:

.. code-block:: bash

    $ nsot protocols list -q foo=test_attribute
    foo-bar01:ospf:3

Replacing an attribute can be done using ``--replace-attributes``:

.. code-block:: bash

    $ nsot protocols update -i 1 --replace-attributes -a foo=test_replace
    [SUCCESS] Updated protocol!

    $ nsot protocols list
    +----------------------------------------------------------------------+
    | ID   Device      Type   Interface         Circuit   Attributes       |
    +----------------------------------------------------------------------+
    | 1    foo-bar01   ospf   foo-bar01:etho0   None      foo=test_replace |
    | 2    foo-bar01   bgp    foo-bar01:etho0   None                       |
    +----------------------------------------------------------------------+

Removing an attribute can be done using ``--delete-attributes``:

.. code-block:: bash

    $ nsot protocols update -i 1 --delete-attributes -a foo=test_replace
    [SUCCESS] Updated protocol!

    $ nsot protocols list
    +----------------------------------------------------------------+
    | ID   Device      Type   Interface         Circuit   Attributes |
    +----------------------------------------------------------------+
    | 1    foo-bar01   ospf   foo-bar01:etho0   None                 |
    | 2    foo-bar01   bgp    foo-bar01:etho0   None                 |
    +----------------------------------------------------------------+

Removing a Protocol can be done by ID and site-id:

.. code-block:: bash

    $ nsot protocols remove -i 1 -s 1
    [SUCCESS] Removed protocol!


Values
======

Values represent attribute values and cannot be directly manipulated. They can
be viewed, however, and this command allows you to do that.

All unique values for a matching Attribute will be displayed.

Displaying values by Attribute name:

.. code-block:: bash

    $ nsot values list --name metro
    chi
    iad
    lax

You might have an Attribute with the same name (e.g. ``metro``) across multiple
:ref:`resource_types`. If you do, you'll want to also filter by resource name:

.. code-block:: bash

    $ nsot values list --name metro --resource-name network
    lax

.. _working_with_changes:

Changes
=======

All Create/Update/Delete events are logged as a Change. A Change includes
information such as the change time, user, and the full resource after
modification. Changes are immutable and can only be removed by deleting the
entire Site.

Listing Changes:

.. code-block:: bash

    $ nsot changes list --site-id 1 --limit 5
    +-----------------------------------------------------------------------+
    | ID   Change At             User               Event    Resource   Obj |
    +-----------------------------------------------------------------------+
    | 73   2015-03-04 11:12:30   jathan@localhost   Delete   Device     1   |
    | 72   2015-03-04 11:10:46   jathan@localhost   Update   Device     1   |
    | 71   2015-03-04 11:06:03   jathan@localhost   Create   Device     7   |
    | 70   2015-03-04 10:56:54   jathan@localhost   Update   Network    6   |
    | 69   2015-03-04 10:53:30   jathan@localhost   Create   Network    6   |
    +-----------------------------------------------------------------------+

When listing a single Change event by ID, you get more detail:

.. code-block:: bash

    $ nsot changes list --site-id 1 --id 73
    +-----------------------------------------------------------------------------------+
    | Change At             User               Event    Resource   ID   Data            |
    +-----------------------------------------------------------------------------------+
    | 2015-03-04 11:12:30   jathan@localhost   Delete   Device     1    attributes:     |
    |                                                                   hostname:potato |
    |                                                                   site_id:1       |
    |                                                                   id:1            |
    +-----------------------------------------------------------------------------------+

Debugging
=========

Is ``-v/--verbose`` just not cutting it? Are you really confused on what's
wrong? Do you want **ALL THE DETAIL**? Then this is for you.

You may toggle debug output by setting the ``PYNSOT_DEBUG`` environment
variable to any true value.

Using the example above:

.. code-block:: bash

    $ export PYNSOT_DEBUG=1

    $ nsot devices add --hostname ''
    DEBUG:pynsot.commands.callbacks:TRANSFORM_ATTRIBUTES [IN]: ()
    DEBUG:pynsot.commands.callbacks:TRANSFORM_ATTRIBUTES [OUT]: {}
    DEBUG:pynsot.client:Reading dotfile.
    DEBUG:pynsot.client:Validating auth_method: auth_header
    DEBUG:pynsot.client:Skipping 'debug' in config for auth_method 'auth_header'
    DEBUG:pynsot.client:Using api_version = 1.0
    DEBUG:pynsot.commands.callbacks:GOT DEFAULT_SITE: 1
    DEBUG:pynsot.commands.callbacks:GOT PROVIDED SITE_ID: None
    DEBUG:pynsot.app:adding {u'bulk_add': None, u'attributes': {}, u'hostname': u'', u'site_id': '1'}
    DEBUG:pynsot.app:rebase: Got site_id: 1
    DEBUG:pynsot.app:rebase: Site_id found; rebasing API URL!
    INFO:requests.packages.urllib3.connectionpool:Starting new HTTP connection (1): localhost
    DEBUG:requests.packages.urllib3.connectionpool:"POST /api/sites/1/devices/ HTTP/1.1" 400 None
    DEBUG:pynsot.app:API ERROR: {u'error': {u'message': {u'hostname': [u'This field may not be blank.']}, u'code': 400}}
    DEBUG:pynsot.app:FORMATTING MESSAGE: {u'hostname': [u'This field may not be blank.']}
    DEBUG:pynsot.app:ERROR MESSAGE = {u'hostname': [u'This field may not be blank.']}
    DEBUG:pynsot.app:PRETTY DICT INCOMING DATA = {u'hostname': [u'This field may not be blank.']}
    DEBUG:pynsot.app:PRETTY DICT INCOMING DATA = {u'bulk_add': None, u'attributes': {}, u'hostname': u''}
    [FAILURE] hostname:  This field may not be blank.

.. tip:: 
    Combine debug output with ``-v/--verbosity`` for MAXIMUM OUTPUT.
