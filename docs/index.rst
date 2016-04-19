###########################################
PyNSoT - The Network Source of Truth Client
###########################################

PyNSoT is the official client library and command-line utility for the
`Network Source of Truth (NSoT)`_ network source-of-truth and IPAM database.
For more information on the core project, please follow the link above.

|Build Status| |Documentation Status| |PyPI Status|

.. _Network Source of Truth (NSoT): https://github.com/dropbox/nsot

.. |Build Status| image:: https://img.shields.io/travis/dropbox/pynsot/master.svg?style=flat
   :target: https://travis-ci.org/dropbox/pynsot
   :width: 88px
.. |Documentation Status| image:: https://readthedocs.org/projects/pynsot/badge/?version=latest&style=flat
   :target: https://readthedocs.org/projects/pynsot/?badge=latest
   :width: 76px
.. |PyPI Status| image:: https://img.shields.io/pypi/v/pynsot.svg?style=flat
   :target: https://pypi.python.org/pypi/pynsot
   :width: 86px

.. warning::
    This project is still very much in flux and likely to have
    backwards-incompatible changes as it evolves with the API for the
    `core project`_.

.. _core project: https://github.com/dropbox/nsot

**Table of Contents**:

.. contents::
   :local:
   :depth: 2

Installation
============

Assuming you've got Python 2.7 and ``pip``, all you have to do is:

.. code-block:: bash

   $ pip install pynsot

We realize that this might not work for you. More detailed install instructions
are Coming Soon™.

Quick Start
===========

How do you use it? Here are some basic examples to get you started.

.. important::
    These examples assume you've already installed and configured ``pynsot``. 
    For a detailed walkthrough, please visit :doc:`config` and then head over
    to the :doc:`cli` docs.

Create a Site
-------------

Sites are namespaces for all other objects. Before you can do anything you'll
need a Site:

.. code-block:: bash

   $ nsot sites add --name 'My Site'

These examples also assume the use of a ``default_site`` so that you don't have
to provide the ``-s/--sit-id`` argument on every query. If this is your only
site, just add ``default_site = 1`` to your ``pynsotrc`` file.

If you're throughoughly lost already, check out the :ref:`example_config`.

CLI Example
-----------

Here's an example of a few basic CLI lookups after adding
several networks:

.. code-block:: bash

   # Add a handful of networks
   $ nsot networks add -c 192.168.0.0/16 -a owner=jathan
   $ nsot networks add -c 192.168.0.0/24
   $ nsot networks add -c 192.168.0.0/25
   $ nsot networks add -c 192.168.0.1/32
   $ nsot networks add -c 172.16.0.0/12
   $ nsot networks add -c 10.0.0.0/24
   $ nsot networks add -c 10.1.0.0/24

   # And start looking them up!
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

API Example
-----------

And for the Python API? Run some Python!

If you want a more detailed walkthrough, check out the :doc:`python_api` guide.

.. code-block:: python

   from pynsot.client import get_api_client

   # get_api_client() is a magical function that returns the proper client
   # according to your ``pynsotrc`` configuration
   c = get_api_client()
   nets = c.sites(1).networks.get()
   subnets = c.sites(1).networks('192.168.0.0/16').subnets.get()
   supernets = c.sites(1).networks('192.168.0.0/24').supernets.get()

Documentation
=============

.. toctree::
   :maxdepth: 2

   config
   cli
   auth
   python_api

API Reference
=============

If you are looking for information on a specific function, class, or
method, go forward.

.. toctree::
   :maxdepth: 2

   api

Miscellaneous Pages
===================

TBD

.. toctree::
   :maxdepth: 2

   changelog


Logo_ by Vecteezy_ is licensed under `CC BY-SA 3.0`_

.. _Logo: https://www.iconfinder.com/icons/532251
.. _Vecteezy: https://www.iconfinder.com/Vecteezy
.. _CC BY-SA 3.0: http://creativecommons.org/licenses/by-sa/3.0/
