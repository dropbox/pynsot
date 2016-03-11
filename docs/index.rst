Welcome to pynsot's documentation!
==================================


Pynsot is the official client library and command-line utility for the
:abbr:`NSoT (Network Source of Truth)` IPAM.  For more information on the core
project, please check it out `here`_.

.. _here: https://github.com/dropbox/nsot

.. warning::
    This project is still very much in flux and likely to have
    backwards-incompatible changes as it evolves with the API for the
    `core project`_.

.. _core project: https://github.com/dropbox/nsot


How do you use it? Here's an example of a few basic CLI lookups after adding
several networks:

.. code-block:: bash

   $ nsot networks add -c 192.168.0.0/16 -a owner=jathan
   $ nsot networks add -c 192.168.0.0/24
   $ nsot networks add -c 192.168.0.0/25
   $ nsot networks add -c 192.168.0.1/32
   $ nsot networks add -c 172.16.0.0/12
   $ nsot networks add -c 10.0.0.0/24
   $ nsot networks add -c 10.1.0.0/24

   $ nsot networks list
   +-------------------------------------------------------------------------+
   | ID   Network       Prefix   Is IP?   IP Ver.   Parent ID   Attributes   |
   +-------------------------------------------------------------------------+
   | 1    192.168.0.0   16       False    4         None        owner=jathan |
   | 2    10.0.0.0      16       False    4         None        owner=jathan |
   | 3    172.16.0.0    12       False    4         None                     |
   | 4    10.0.0.0      24       False    4         2                        |
   | 5    10.1.0.0      24       False    4         2                        |
   +-------------------------------------------------------------------------+

   $ nsot networks list --include-ips
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

   $ nsot networks list --include-ips --no-include-networks
   +-----------------------------------------------------------------------+
   | ID   Network       Prefix   Is IP?   IP Ver.   Parent ID   Attributes |
   +-----------------------------------------------------------------------+
   | 6    192.168.0.1   32       True     4         1                      |
   +-----------------------------------------------------------------------+

   $ nsot networks list --cidr 192.168.0.0/16 subnets
    +-----------------------------------------------------------------------+
    | ID   Network       Prefix   Is IP?   IP Ver.   Parent ID   Attributes |
    +-----------------------------------------------------------------------+
    | 6    192.168.0.0   24       False    4         1                      |
    | 7    192.168.0.0   25       False    4         6                      |
    +-----------------------------------------------------------------------+

    $ nsot networks list -c 192.168.0.0/24 supernets
    +-------------------------------------------------------------------------+
    | ID   Network       Prefix   Is IP?   IP Ver.   Parent ID   Attributes   |
    +-------------------------------------------------------------------------+
    | 1    192.168.0.0   16       False    4         None        owner=jathan |
    |                                                            cluster=     |
    |                                                            foo=baz      |
    +-------------------------------------------------------------------------+


And for the Python API?

.. code-block:: python

   from pynsot.client import get_api_client

   # get_api_client is a magical function that returns the proper client
   # according to your pynsotrc configuration
   c = get_api_client()
   nets = c.sites(1).networks.get()
   subnets = c.sites(1).networks('192.168.0.0/16').subnets.get()
   supernets = c.sites(1).networks('192.168.0.0/24').supernets.get()


You can install by running ``pip install pynsot``!


Documentation Contents
----------------------

.. toctree::
   :maxdepth: 2

   config
   cli
   auth
   python_api

API Reference
-------------

If you are looking for information on a specific function, class, or
method, go forward.

.. toctree::
   :maxdepth: 2

   api

Miscellaneous Pages
-------------------

.. toctree::
   :maxdepth: 2

   changelog
