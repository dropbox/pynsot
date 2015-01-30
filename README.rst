######
pynsot
######

Python client for NSoT REST API.

Using
=====

All of the endpoints are dynamic, so it's like magic. Literally::

    >>> from pynsot.client import Client
    >>> email = 'jathan@localhost'
    >>> url = 'http://localhost:8990/api'
    >>> api = Client(url, email=email)
    >>> print api.users.get()
    >>> print api.sites(1).get()
    >>> print api.sites(1).attributes.get()


CLI Exampless
=============

Sites
-----

Adding a site::

    $ ./nsot sites add --name Spam --description 'Spam Site'
    Successfully added site (id: 4) with args: description='Spam Site', name='Spam'!

Listing all sites::

    $ ./nsot sites list
    description    name      id
    -------------  ------  ----
    Foo site       Foo        1
    Bar Site       Bar        2
    Baz Site       Baz        3
    Spam Site      Spam       4

Listing a single site::

    $ ./nsot sites list --name Foo
    description    name      id
    -------------  ------  ----
    Foo site        Foo        1

Removing a site::

    $ ./nsot sites remove -i 1
    Successfully removeed site with args: id=u'1'!

Networks
--------

NYI

Attributes
----------

NYI
