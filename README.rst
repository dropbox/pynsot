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

::

    $ ./nsot sites add --name Spam --description 'Spam Site'
    Successfully added site (id: 4) with args: description='Spam Site', name='Spam'!

::

    $ ./nsot sites list
    description    name      id
    -------------  ------  ----
    Foo site       Foo        1
    Bar Site       Bar        2
    Baz Site       Baz        3
    Spam Site      Spam       4

::

    $ ./nsot sites list --name Foo
    description    name      id
    -------------  ------  ----
