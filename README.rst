######
pynsot
######

.. image:: https://travis-ci.org/dropbox/pynsot.svg
    :target: https://travis-ci.org/dropbox/pynsot

Python client library and command-line utility for the `Network Source of
Truth <https://github.com/dropbox/nsot>`_ (NSoT) REST API.

Warning
=======

This project is still very much in flux and likely to have
backwards-incompatible changes as it evolves with the API for the `Network
Source of Truth <https://github.com/dropbox/nsot>`_ project.

Using
=====

All of the endpoints are dynamic, so it's like magic. Literally::

    $ python
    >>> from pynsot.client import EmailHeaderClient
    >>> email = 'jathan@localhost'
    >>> url = 'http://localhost:8990/api'
    >>> api = EmailHeaderClient(url, email=email)
    >>> print api.users.get()
    >>> print api.sites(1).get()
    >>> print api.sites(1).attributes.get()

Authentication
--------------

The default method of authentication for NSoT is ``auth_token`` and this is what
the client uses. You'll need to retreive your ``secret_key`` from the NSoT web
interface for this to work::

    $ python
    >>> from pynsot.client import Client
    >>> email = 'jathan@localhost'
    >>> secret_key = 'qONJrNpTX0_9v7H_LN1JlA0u4gdTs4rRMQklmQF9WF4='
    >>> url = 'http://localhost:8990/api'
    >>> api = Client(url, email=email, secret_key=secret_key)

Config
------

By default, the ``nsot`` command-line utility will read your settings from
``~/.pynsotrc``, which looks like this::

    $ cat ~/.pynsotrc
    [pynsot]
    url = http://localhost:8990/api
    email = jathan@localhost
    secret_key = qONJrNpTX0_9v7H_LN1JlA0u4gdTs4rRMQklmQF9WF4=
    auth_method = auth_token

You can create it yourself, or you'll be prompted to create one if it isn't
found the first time you use the ``nsot`` utility::

    $ nsot sites list
    /home/jathan/.pynsotrc not found; would you like to create it? [Y/n]: y
    Please enter URL: http://localhost:8990/api
    Please enter SECRET_KEY: qONJrNpTX0_9v7H_LN1JlA0u4gdTs4rRMQklmQF9WF4=
    Please enter EMAIL: jathan@localhost

.. _default_site:

Default Site
~~~~~~~~~~~~

You may optionally specify a ``default_site`` setting within your
``~/.pynsotrc`` that will pass along the designated ``site_id`` on your behalf
any time the ``-s/--site-id`` option is required::

   [pynsot]
   ; ... Other settings ...
   default_site = 1

Since most users will only have a single site they care about, this is to make
your life easier. If you do have multiple sites, you can still provide the
``-s/--site-id`` option to override your ``default_site``.

CLI Usage
=========

Every resource type has four eligible actions representing creation,
retrieval, update, and removal:

+ add
+ list
+ remove
+ update

.. note::
   The only exception are Change events, which are immutable and can only be
   viewed.

Each resource can be manipulated using positional command arguments::

    $ nsot
    Usage: nsot [OPTIONS] COMMAND [ARGS]...

      Network Source of Truth (NSoT) command-line utility.

    Options:
      -v, --verbose  Toggle verbosity.
      --version      Show the version and exit.
      -h, --help     Show this message and exit.

    Commands:
      attributes  Attribute objects.
      changes     Change events.
      devices     Device objects.
      networks    Network objects.
      sites       Site objects.

The actions for each resource have varying options and requirements which will
be covered a little later. For example, to work with Sites you would run ``nsot
sites``::

    $ nsot sites
    Usage: nsot sites [OPTIONS] COMMAND [ARGS]...

      Site objects.

      Sites are the top-level resource from which all other resources descend.
      In other words, Sites contain Attributes, Changes, Devices, and Networks.

    Options:
      -h, --help  Show this message and exit.

    Commands:
      add     Add a new Site.
      list    List existing Sites.
      remove  Remove a Site.
      update  Update a Site.

Getting Help
------------

Every resource and action for each resource has help text that can be accessed
using the ``-h/--help`` option. Use it!

Required Options
----------------

When adding objects, certain fields will be required. The required options will
be designated as such with a ``[required]`` tag in the help text (for example
from ``nsot sites add --help``::

    -n, --name NAME         The name of the Site.  [required]

If a required option is not provided, ``nsot`` will complain::

    Error: Missing option "-n" / "--name".

Site ID
-------

For all resources other than Sites, the ``-s/--site-id`` option is required to
specify which Site you would like the object to be under. (See:
`default_site`)

Updating or Removing Objects
----------------------------

When updating or removing objects, you must provide their unique ID using the
``-i/--id`` option. The object's ID can be obtained by using the ``list``
action.

Viewing Objects
---------------

Each resource's ``list`` action supports ``-i/--id``, ``-l/--limit`` and
``-o/--offset`` options.

+ The ``-i/--id`` option will retrieve a single object by the provided unique
  ID and will override any other list options.
+ The ``-l/--limit`` option will limit the set of results to ``N`` resources.
+ The ``-o/--offset`` option will skip the first ``N`` resources.

Set Queries
~~~~~~~~~~~

The Device and Network resources support a ``-q/--query`` option that is a
representation of set operations for matching attribute/value pairs.

The operations are evaluated from left-to-right, where the first character indicates the
set operation:

+ "+" indicates a set union
+ "-" indicates a set difference
+ no marker indicates a set intersection

For example

+ ``-q "foo=bar"`` would return the set intersection of objects with ``foo=bar``.
+ ``-q "foo=bar -owner=jathan"`` would return the set difference of all objects
  with ``foo=bar`` (that is all ``foo=bar`` where ``owner`` is not ``jathan``).
+ ``-q "foo=bar +foo=baz`` would return the set union of all objects with
  ``foo=bar`` or ``foo=baz`` (that is all objects matching either).

The ordering of these operations is important. If you are not familiar with set
operations, please check out `Basic set theory concepts and notation
<http://en.wikipedia.org/wiki/Set_theory#Basic_concepts_and_notation>`_
(Wikipedia).

Bulk Addition of Objects
------------------------

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
~~~~~~~~~~

Sample file for ``nsot devices add --bulk-add /tmp/attributes``::

    name:resource_name:required:description:multi:display
    owner:Network:True:Network owner:True:True
    metro:Device:False:Device metro:False:True

Devices
~~~~~~~

Sample file for ``nsot devices add --bulk-add /tmp/devices``::

    hostname:attributes
    device5:foo=bar,owner=team-networking
    device6:foo=bar,owner=team-networking

Networks
~~~~~~~~

Sample file for ``nsot networks add --bulk-add /tmp/networks``::

    cidr:attributes
    10.20.30.0/24:foo=bar,owner=team-networking
    10.20.31.0/24:foo=bar,owner=team-networking

Working with Resources
======================

Sites
-----

Sites are the top-level resource from which all other resources descend. In
other words, Sites contain Networks, Attributes, Devices, etc. These examples
illustrate having many Sites.

Adding a site::

    $ nsot sites add --name Spam --description 'Spam Site'
    [SUCCESS] added site with args: name=Space, description=Spam Site!

Listing all Sites::

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

Listing a single Site::

    $ nsot sites list --name Foo
    +-------------------------+
    | ID   Name   Description |
    +-------------------------+
    | 1    Foo    Foo Site    |
    +-------------------------+

Listing a few Sites::

    $ nsot sites list --limit 2
    +--------------------------+
    | ID   Name    Description |
    +--------------------------+
    | 1    Foo     Foo Site    |
    | 2    Bar     Bar Site    |
    +--------------------------+

Updating a Site::

    $ nsot sites update --id 2 --name Snickers
    [SUCCESS] updated site with args: description=None, name=Snickers!

    $ nsot sites list --name Snickers
    +-----------------------------+
    | ID   Name       Description |
    +-----------------------------+
    | 2    Snickers   Bar Site    |
    +-----------------------------+

Removing a Site::

    $ nsot sites remove --id 1
    [SUCCESS] removed site with args: id=1!

Attributes
----------

Attributes are flexible key/value pairs or tags you may use to assign arbitrary
data to objects.

.. note::
    Before you may assign Attributes to other resources, you must create the
    Attribute first!

Adding an Attribute::

    $ nsot attributes add --site-id 1 -n owner --r Device -d "Owner of a device." --required
    [SUCCESS] Added attribute with args: multi=False, resource_name=Device, name=owner, required=True, display=False, description=Owner of a device.!

Listing all Attributes::

    $ nsot attributes list --site-id 1
    +-----------------------------------------------------------------------------+
    | ID   Name    Resource   Required?   Display?   Multi?   Description         |
    +-----------------------------------------------------------------------------+
    | 3    owner   Device     True        False      False    Owner of a device.  |
    | 4    foo     Network    False       False      False    Foo for devices     |
    | 2    owner   Network    False       False      False    Owner of a network. |
    +-----------------------------------------------------------------------------+

You may also list Attributes by name::

    $ nsot attributes list --site-id 1 --name owner
    +-----------------------------------------------------------------------------+
    | ID   Name    Resource   Required?   Display?   Multi?   Description         |
    +-----------------------------------------------------------------------------+
    | 3    owner   Device     False       True       False    Owner of a device.  |
    | 2    owner   Network    False       False      False    Owner of a network. |
    +-----------------------------------------------------------------------------+

When listing a single Attribute by ID, you get more detail::

    $ nsot attributes list --site-id 1 --id 3
    +--------------------------------------------------------------------------------------+
    | Name    Resource   Required?   Display?   Multi?   Constraints         Description   |
    +--------------------------------------------------------------------------------------+
    | owner   Device     False       False      False    pattern=            Device owner. |
    |                                                    valid_values=                     |
    |                                                    allow_empty=False                 |
    +--------------------------------------------------------------------------------------+

Updating an Attribute::

    $ nsot attributes update --site-id 1 --id 3 --no-required
    [SUCCESS] Updated attribute with args: multi=None, description=None, required=False, display=None!

    $ nsot attributes list --site-id 1 --id 3
    +----------------------------------------------------------------------------+
    | ID   Name    Resource   Required?   Display?   Multi?   Description        |
    +----------------------------------------------------------------------------+
    | 3    owner   Device     False       False      False    Owner of a device. |
    +----------------------------------------------------------------------------+

Removing an Attribute::

    $ nsot attributes remove --site-id 1 --id 6
    [SUCCESS] Removed attribute with args: id=6!

Networks
--------

A Network resource can represent an IP Network or an IP Address. Working with
networks is usually done with CIDR notation. Networks can have any number of
arbitrary Attributes.

Adding a Network::

    $ nsot networks add --site-id 1 --cidr 192.168.0.0/16 --attributes owner=jathan
    [SUCCESS] Added network with args: attributes={u'owner': u'jathan'}, cidr=192.168.0.0/16!

Listing Networks::

    $ nsot networks list --site-id 1
    +-------------------------------------------------------------------------+
    | ID   Network       Prefix   Is IP?   IP Ver.   Parent ID   Attributes   |
    +-------------------------------------------------------------------------+
    | 1    192.168.0.0   16       False    4         None        owner=jathan |
    | 2    10.0.0.0      16       False    4         None        owner=jathan |
    | 3    172.16.0.0    12       False    4         None                     |
    | 4    10.0.0.0      24       False    4         2                        |
    | 5    10.1.0.0      24       False    4         2                        |
    +-------------------------------------------------------------------------+

You may also optionally include IP addresses with ``--include-ips``::

    $ nsot networks list --side-id 1 --include-ips
    +-------------------------------------------------------------------------+
    | ID   Network       Prefix   Is IP?   IP Ver.   Parent ID   Attributes   |
    +-------------------------------------------------------------------------+
    | 1    192.168.0.0   16       False    4         None        owner=jathan |
    | 2    10.0.0.0      16       False    4         None        owner=jathan |
    | 3    172.16.0.0    12       False    4         None                     |
    | 4    10.0.0.0      24       False    4         2                        |
    | 5    10.1.0.0      24       False    4         2                        |
    | 6    192.168.0.1   32       True     4         1                        |
    +-------------------------------------------------------------------------+

Or, you may show only IP adddresses by using ``--include-ips`` with
``--no-include-networks``::

    $ nsot networks list --site-id 1 --include-ips --no-include-networks
    +-----------------------------------------------------------------------+
    | ID   Network       Prefix   Is IP?   IP Ver.   Parent ID   Attributes |
    +-----------------------------------------------------------------------+
    | 6    192.168.0.1   32       True     4         1                      |
    +-----------------------------------------------------------------------+

Performing a set query on Networks by attribute/value::

    $ nsot networks list --site-id 1 --query owner=jathan
    10.0.0.0/16
    192.168.0.0/16

Updating a Network (``-a/--attributes`` can be provide once for each Attribute)::

    $ nsot networks update --site-id 1 --id 1 -a owner=jathan -a foo=bar
    [SUCCESS] Updated network with args: attributes={u'owner': u'nobody', u'foo': u'bar'}!

    $ nsot networks list --site-id 1 --id 6
    +-------------------------------------------------------------------------+
    | ID   Network       Prefix   Is IP?   IP Ver.   Parent ID   Attributes   |
    +-------------------------------------------------------------------------+
    | 1    192.168.0.0   16       False    4         None        owner=nobody |
    |                                                            foo=bar      |
    +-------------------------------------------------------------------------+

Removing a Network::

    $ nsot networks remove --site-id 1 --id 2
    [SUCCESS] Removed network with args: id=2!

Supernets
~~~~~~~~~

Given a Network ``192.168.0.0/24``::

    $ nsot networks list --site-id 1 --id 6
    +-----------------------------------------------------------------------+
    | ID   Network       Prefix   Is IP?   IP Ver.   Parent ID   Attributes |
    +-----------------------------------------------------------------------+
    | 6    192.168.0.0   24       False    4         1                      |
    +-----------------------------------------------------------------------+

You may view the networks that contain that Network (aka supernets)::

    $ nsot networks list --site-id 1 --id 5 supernets
    +-------------------------------------------------------------------------+
    | ID   Network       Prefix   Is IP?   IP Ver.   Parent ID   Attributes   |
    +-------------------------------------------------------------------------+
    | 1    192.168.0.0   16       False    4         None        owner=jathan |
    |                                                            cluster=     |
    |                                                            foo=baz      |
    +-------------------------------------------------------------------------+

Subnets
~~~~~~~

Given the parent Network from the above example (``192.168.0.0/16``), you may
the view Networks it contains (aka subnets)::

    $ nsot networks list --site-id 1 --id 1 subnets
    +-----------------------------------------------------------------------+
    | ID   Network       Prefix   Is IP?   IP Ver.   Parent ID   Attributes |
    +-----------------------------------------------------------------------+
    | 6    192.168.0.0   24       False    4         1                      |
    | 7    192.168.0.0   25       False    4         6                      |
    +-----------------------------------------------------------------------+

Devices
-------

A Device represents various hardware components on your network such as
routers, switches, console servers, PDUs, servers, etc.

Devices also support arbitrary attributes similar to Networks.

Adding a Device::

    $ nsot devices add --site-id 1 --hostname foo-bar1 --attributes owner=neteng
    [SUCCESS] Added device with args: attributes={u'owner': u'neteng'}, hostname=foo-bar1!

Listing Devices::

    $ nsot devices list --site-id 1
    +------------------------------+
    | ID   Hostname   Attributes   |
    +------------------------------+
    | 1    foo-bar1   owner=jathan |
    | 2    foo-bar2   owner=neteng |
    | 3    bar-baz1   owner=jathan |
    | 4    bar-baz2   owner=neteng |
    +------------------------------+

Performing a set query on Device by attribute/value::

    $ nsot networks list --site-id 1 --query owner=neteng
    bar-baz2
    foo-bar2

Updating a Device::

    $ nsot devices update --id 1 --hostname potato
    [SUCCESS] Updated device with args: attributes={}, hostname=potato!

    $ ./nsot devices list --site-id 1 --id 1
    +----------------------------+
    | ID   Hostname   Attributes |
    +----------------------------+
    | 1    potato                |
    +----------------------------+

Removing a Device::

    $ nsot devices remove --site-id 1 --id 1
    [SUCCESS] Removed device with args: id=1!

Changes
-------

All Create/Update/Delete events are logged as a Change. A Change includes
information such as the change time, user, and the full resource after
modification. Changes are immutable and can only be removed by deleting the
entire Site.

Listing Changes::

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

When listing a single Change event by ID, you get more detail::

    $ nsot changes list --site-id 1 --id 73
    +-----------------------------------------------------------------------------------+
    | Change At             User               Event    Resource   ID   Data            |
    +-----------------------------------------------------------------------------------+
    | 2015-03-04 11:12:30   jathan@localhost   Delete   Device     1    attributes:     |
    |                                                                   hostname:potato |
    |                                                                   site_id:1       |
    |                                                                   id:1            |
    +-----------------------------------------------------------------------------------+
