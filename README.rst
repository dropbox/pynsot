######
pynsot
######

Python client for NSoT REST API.

Using
=====

All of the endpoints are dynamic, so it's like magic. Literally::

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

    >>> from pynsot.client import Client
    >>> email = 'jathan@localhost'
    >>> secret_key = 'qONJrNpTX0_9v7H_LN1JlA0u4gdTs4rRMQklmQF9WF4='
    >>> url = 'http://localhost:8990/api'
    >>> api = Client(url, email=email, secret_key=secret_key)

Config
------

By default, the ``nsot`` command will read your settings from ``~/.pynsotrc``,
which looks like this::

    $ cat ~/.pynsotrc
    [pynsot]
    url = http://localhost:8990/api
    email = jathan@localhost    
    secret_key = qONJrNpTX0_9v7H_LN1JlA0u4gdTs4rRMQklmQF9WF4=
    auth_method = auth_token

You can create it yourself, or you'll be prompted to create one if it isn't
found::

    $ nsot sites list
    /home/jathan/.pynsotrc not found; would you like to create it? [Y/n]: y
    Please enter URL: http://localhost:8990/api
    Please enter SECRET_KEY: qONJrNpTX0_9v7H_LN1JlA0u4gdTs4rRMQklmQF9WF4=
    Please enter EMAIL: jathan@localhost

CLI Exampless
=============

Sites
-----

Adding a site::

    $ nsot sites add --name Spam --description 'Spam Site'
    [SUCCESS] added site with args: name=u'Space', description=u'Spam Site'!

Listing all sites::

    $ nsot sites list
      ID  Name    Description
    ----  ------  -------------
       1  Foo     Foo site
       2  Bar     Bar Site
       3  Baz     Baz Site
       4  Spam    Spam Site
       6  Sheep   Sheep site

Listing a single site::

    $ ./nsot sites list --name Foo
      ID  Name    Description
    ----  ------  -------------
       1  Foo     Foo site

Listing a few sites::

    $ nsot sites list --limit 2
      ID  Name    Description
    ----  ------  -------------
       1  Foo     Foo site
       2  Bar     Bar Site

Updating a site::

    $ nsot sites update --id 2 --name Snickers
    [SUCCESS] updated site with args: description=None, name=u'Snickers'!

    $ nsot sites list --name Snickers
      ID  Name      Description
    ----  --------  -------------
       2  Snickers  Bar Site

Removing a site::

    $ nsot sites remove --id 1
    [SUCCESS] removed site with args: id=u'1'!

Networks
--------

NYI

Attributes
----------

NYI
