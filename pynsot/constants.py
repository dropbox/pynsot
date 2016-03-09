# -*- coding: utf-8 -*-

"""
Constant values used across the project.
"""

from __future__ import unicode_literals
import os


__author__ = 'Jathan McCollum'
__maintainer__ = 'Jathan McCollum'
__email__ = 'jathan@dropbox.com'
__copyright__ = 'Copyright (c) 2016 Dropbox, Inc.'


# Header used for passthrough authentication.
AUTH_HEADER = 'X-NSoT-Email'

# Default authentication method
DEFAULT_AUTH_METHOD = 'auth_token'

# Mapping of required field names and default values we want to be in the
# dotfile.
REQUIRED_FIELDS = {
    'auth_method': ['auth_token', 'auth_header'],
    'url': None,
}

# Fields that map to specific auth_methods.
SPECIFIC_FIELDS = {
    'auth_header': {
        'default_domain': 'localhost',
        'auth_header': AUTH_HEADER,
    }
}

# Mapping of optional field names and default values (if any)
OPTIONAL_FIELDS = {
    'default_site': None,
    'api_version': None,
}

# Path stuff
USER_HOME = os.path.expanduser('~')
DOTFILE_NAME = '.pynsotrc'
DOTFILE_PATH = os.path.join(USER_HOME, DOTFILE_NAME)
DOTFILE_PERMS = 0600  # -rw-------

# Config section name
SECTION_NAME = 'pynsot'
