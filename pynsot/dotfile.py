"""
Handle the read, write, and generation of the .pynsotrc config file.
"""

__author__ = 'Jathan McCollum'
__maintainer__ = 'Jathan McCollum'
__email__ = 'jathan@dropbox.com'
__copyright__ = 'Copyright (c) 2015 Dropbox, Inc.'


from ConfigParser import RawConfigParser

import logging
import os

from .vendor import click
from .vendor import rcfile


# Logging object
log = logging.getLogger(__name__)

# Default authentication method (one of user_auth_header, auth_token)
AUTH_METHOD = 'auth_token'

# Mapping of required field names and default values we want to be in the
# dotfile.
REQUIRED_FIELDS = {
    'auth_method': AUTH_METHOD,
    'url': None,
    'email': None,
    'secret_key': None,
}

# Path stuff
USER_HOME = os.path.expanduser('~')
DOTFILE_NAME = '.pynsotrc'
DOTFILE_PATH = os.path.join(USER_HOME, DOTFILE_NAME)
DOTFILE_PERMS = 0600  # -rw-------

# Config section name
SECTION_NAME = 'pynsot'


__all__ = (
    'DotfileError', 'Dotfile',
)


class DotfileError(Exception):
    """Raised when something with the dotfile fails."""


class Dotfile(object):
    """Create, read, and write a dotfile."""
    def __init__(self, filepath=DOTFILE_PATH, **kwargs):
        self.filepath = filepath

    def read(self, **kwargs):
        """
        Read ``~/.pynsotrc`` and return it as a dict.
        """
        config = rcfile.rcfile(SECTION_NAME, args={'config': self.filepath})
        config.pop('config', None)  # We don't need this field in here.

        # If there is *no* config data so far and...
        if not config and not os.path.exists(self.filepath):
            p = '%s not found; would you like to create it?' % (self.filepath,)
            if click.confirm(p, default=True, abort=True):
                config_data = self.get_config_data(**kwargs)
                self.write(config_data)

        self.config = config

        # If we have configuration values, validate the permissions and presence
        # of fields in the dotfile
        if self.config.get('auth_method') == 'auth_token':
            self.validate_perms()
            self.validate_fields(config)

        return config

    def validate_perms(self):
        """Make sure dotfile ownership and permissions are correct."""
        if not os.path.exists(self.filepath):
            return None

        # Ownership
        s = os.stat(self.filepath)
        if s.st_uid != os.getuid():
            msg = '%s: %s must be owned by you' % (DOTFILE_NAME, self.filepath)
            raise DotfileError(msg)

        # Permissions
        self.enforce_perms()

    def validate_fields(self, field_names):
        """
        Make sure all the fields are set.

        :param field_names:
            List of field names to validate
        """
        for rname in sorted(REQUIRED_FIELDS):
            if rname not in field_names:
                msg = '%s: Missing required field: %s' % (self.filepath, rname)
                raise DotfileError(msg)

    def enforce_perms(self, perms=DOTFILE_PERMS):
        """
        Enforce permissions on the dotfile.

        :param perms:
            Octal number representing permissions to enforce
        """
        log.debug('Enforcing permissions %o on %s' % (perms, self.filepath))
        os.chmod(self.filepath, perms)

    def write(self, config_data, filepath=None):
        """
        Create a dotfile from keyword arguments.

        :param config_data:
            Dict of config settings

        :param filepath:
            (Optional) Path to write
        """
        if filepath is None:
            filepath = self.filepath
        config = RawConfigParser()
        section = SECTION_NAME
        config.add_section(section)

        # Set the config settings
        for key, val in config_data.iteritems():
            config.set(section, key, val)

        with open(filepath, 'wb') as dotfile:
            config.write(dotfile)

        self.enforce_perms()
        log.debug('wrote %s' % filepath)

    @staticmethod
    def get_config_data(required_fields=REQUIRED_FIELDS, **kwargs):
        """
        Enumerate required fields and prompt for ones that weren't provided if
        they don't have default values.

        :param required_fields:
            Mapping of required field names to default values

        :param kwargs:
            Dict of config settings
        """
        config_data = {}
        for field, default_value in required_fields.iteritems():
            # If the field was not provided and does not have a default value
            # prompt for it
            if field not in kwargs and default_value is None:
                prompt = 'Please enter %s' % (field.upper(),)
                value = click.prompt(prompt, type=str)
            # Or, use the provided value
            elif field in kwargs:
                value = kwargs[field]
            # Otherwise, use the default value
            else:
                value = default_value

            config_data[field] = value
        return config_data
