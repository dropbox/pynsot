#########
Changelog
#########

Version History
===============

.. _v1.1.2:

1.1.2 (2017-02-06)
-----------------

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
