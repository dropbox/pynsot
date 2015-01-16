######
pynsot
######

Python client for NSoT REST API.

Using
=====

All of the endpoints are dynamic, so it's like magic. Literally::

    >>> import pynsot
    >>> email = 'jathan@localhost'
    >>> url = 'http://localhost:8990/api'
    >>> api = pynsot.NsotAPI(url, email=email)
    >>> print api.users.get()
    >>> print api.sites(1).get()
    >>> print api.sites(1).network_attributes.get()
