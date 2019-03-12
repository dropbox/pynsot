#########
Changelog
#########

Version History
===============

.. _v1.3.2:

1.3.2 (2019-03-11)

* Update pynsot to use Click 7.x and explicitly name subcommands with
  underscores as such so they don't get updated to use hyphens.
* Fix #159 - Add ``--limit`` and ``--offset`` to ``Protocol`` and
  ``ProtocolType`` CLI. These CLI opt ions are standard across all resource
  types with their ``list`` subcommands, but they were forgotten with the new
  ``Protocol`` and ``ProtocolType`` objects.

.. _v1.3.1:

1.3.1 (2018-09-11)
------------------

* Fixes NSoT Issue #121: Enabling `force_delete` flag for deleting parent networks.
* Adds `development` section to docs to explain versioning and the release process.
* Fixes miscellaneous typos.

.. _v1.3.0:

1.3.0 (2018-03-20)
------------------

* Implements protocols and protocol_types CLI capability (added in NSoT v1.3.0).
* Enhancement to ``-g/--grep`` to include all object fields.
* Fixes #149: Add set queries to `nsot circuits list`.

.. _v1.2.1:

1.2.1 (2017-09-07)
------------------

* Implements #142: Sorts the ``Attributes`` column in the output of the
  ``list`` subcommand, similar to the output of the ``list`` subcommand
  with the ``-g`` flag.

.. _v1.2.0:

1.2.0 (2017-07-28)
------------------

.. danger::

    This release requires NSoT version 1.2.0 and is **BACKWARDS INCOMPATIBLE**
    with previous NSoT versions.

* Adds support for natural keys when creating/updating related objects (added in
  NSoT v1.2.0)
* Interfaces may now be created/updated by referencing the device
  hostname or device ID
* Circuits may now be created/updated by referencing the interfaces by
  natural key (slug) OR interface ID
* The visual display of Networks, Interfaces, Circuits has been updated to be
  more compact/concise

  + Networks

    - cidr is now displayed instead of network_address/prefix_length
    - parent cidr is now displayed instead of parent_id

  + Interfaces

    - name_slug is now displayed instead of device_id/name
    - parent name is now displayed instead of parent_id

  + Circuits

    - interface slugs are now displayed instead of ID numbers

* The string "(Key)" is now displayed in the header for the natural key field
  of a resource on list views

.. _v1.1.4:

1.1.4 (2017-05-31)
------------------

* Add commands for Interface tree traversal (added in NSoT 1.1.4)

.. _v1.1.3:

1.1.3 (2017-02-21)
------------------

* Fix #119 - Add ability to use set queries on `list` subcommands (#133)

.. _v1.1.2:

1.1.2 (2017-02-06)
------------------

* Add support for strict allocations (added in NSoT v1.1.2)
* Change requirements.txt to use Compatible Release version specifiers

.. _v1.1.1:

1.1.1 (2017-01-31)
------------------

* Corrected the spelling for the ``descendants`` sub-command on Networks. The
  old misspelled form of ``descendents`` will display a warning to users.

.. _v1.1.0:

1.1.0 (2017-01-30)
------------------

* Adds support for Circuit objects (added in NSoT v1.1)

.. _v1.0.2:

1.0.2 (2017-01-23)
------------------

* Bump NSoT requirement to v1.0.13, fix tests that were broken
* Fix #125 - Support natural key when working with interface. Interfaces can
  now be referred to using `device_name:interface_name` in addition to the
  unique ID given by the database.

.. _v1.0.1:

1.0.1 (2016-12-12)
------------------

* Network objects are now properly sorted by network hierarchy instead of by
  alphanumeric order.
* Streamlined the way that objects are displayed by natural key to simplify
  future feature development.

.. _v1.0:

1.0 (2016-04-27)
----------------

* OFFICIAL VERSION 1.0!
* Fully compatible with NSoT REST API version 1
