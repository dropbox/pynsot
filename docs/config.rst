Configuration
=============

Configuration for pynsot consists of a single INI with two possible locations:

1. ``/etc/pynsotrc``
2. ``~/.pynsotrc``

The home directory takes precedence. Configuration elements must be under the
``pynsot`` section.

If you don't create this file, don't fret - running ``nsot`` will prompt you to
create one interactively.

Like so::

    $ nsot sites list
    /home/jathan/.pynsotrc not found; would you like to create it? [Y/n]: y
    Please enter URL: http://localhost:8990/api
    Please enter SECRET_KEY: qONJrNpTX0_9v7H_LN1JlA0u4gdTs4rRMQklmQF9WF4=
    Please enter EMAIL: jathan@localhost

Example Configuration::

    [pynsot]
    auth_header = X-NSoT-Email
    auth_method = auth_header
    default_site = 1
    default_domain = company.com
    url = https://nsot.company.com/api


.. _config_ref:

.. list-table:: Configuration reference
   :header-rows: 1

   *  - Key
      - Value
      - Default
      - Required
   *  - url
      - API URL. Eg: http://localhost:8990/api
      -
      - Yes
   *  - email
      - User email
      - $USER@default_domain
      - No
   *  - api_version
      - API version to use. Eg: 1.0
      - None
      - No
   *  - auth_method
      - auth_token or auth_header
      -
      - Yes
   *  - secret_key
      - token from your user profile
      -
      - No
   *  - default_site
      - default site id when you don't explicitly say
      -
      - No
   *  - auth_header
      - HTTP header to send email in to url.
      - X-NSoT-Email
      - No
   *  - default_domain
      - Domain for email address. Eg: example.com
      - localhost
      - No
