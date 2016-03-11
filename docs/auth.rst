Authentication
==============

NSoT supports two methods of authentication and these are implemented in the
client:

1. ``auth_token``
2. ``auth_header``

The client default is ``auth_token``, but ``auth_header`` is more flexible for
"zero touch" use.

If sticking with the defaults, you'll need to retrieve your key from
``/profile`` in the web interface.

Client
------

.. note::
    The preferred method is to configure your pynsotrc as you wish and then use
    ``pynsot.client.get_api_client`` for easier code re-use. Should you need
    something more manual, proceed

Following will show you how to set up a client object in Python:

.. code-block:: python

   from pynsot.client import AuthTokenClient, EmailHeaderClient, get_api_client

   # PREFERRED
   c = get_api_client()

   # OR

   email = 'jathan@localhost'
   secret_key = 'qONJrNpTX0_9v7H_LN1JlA0u4gdTs4rRMQklmQF9WF4='
   url = 'http://localhost:8990/api'
   c = Client(url, email=email, secret_key=secret_key)

   # OR
   domain = 'localhost'
   auth_header = 'X-NSoT-Email'
   c = EmailHeaderClient(
       url,
       email=email,
       default_domain=domain,
       auth_header=auth_header,
   )

