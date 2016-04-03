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

Refer to :ref:`config_ref` for setting these in your ``pynsotrc``

Python Client
-------------

Assuming your configuration is correct, the CLI interface doesn't need anything
special to make authentication work. The following only applies to retrieving a
client instance in Python.

.. code-block:: python

   from pynsot.client import AuthTokenClient, EmailHeaderClient, get_api_client

   # This is the preferred method, returning the appropriate client according
   # to your dotfile if no arguments are supplied.
   #
   # Alteratively you can override options by passing url, auth_method, and
   # other kwargs. See `help(get_api_client) for more details
   c = get_api_client()

   # OR using the client objects directly

   email = 'jathan@localhost'
   secret_key = 'qONJrNpTX0_9v7H_LN1JlA0u4gdTs4rRMQklmQF9WF4='
   url = 'http://localhost:8990/api'
   c = AuthTokenClient(url, email=email, secret_key=secret_key)

   # Email Header Client
   domain = 'localhost'
   auth_header = 'X-NSoT-Email'
   c = EmailHeaderClient(
       url,
       email=email,
       default_domain=domain,
       auth_header=auth_header,
   )

