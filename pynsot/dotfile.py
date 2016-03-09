# -*- coding: utf-8 -*-

"""
Handle the read, write, and generation of the .pynsotrc config file.
"""

from __future__ import unicode_literals
from ConfigParser import RawConfigParser
import copy
import logging
import os

from .vendor import click
from .vendor import rcfile
from . import constants


__author__ = 'Jathan McCollum'
__maintainer__ = 'Jathan McCollum'
__email__ = 'jathan@dropbox.com'
__copyright__ = 'Copyright (c) 2015-2016 Dropbox, Inc.'


# Logging object
log = logging.getLogger(__name__)


__all__ = (
    'DotfileError', 'Dotfile',
)


class DotfileError(Exception):
    """Raised when something with the dotfile fails."""


class Dotfile(object):
    """Create, read, and write a dotfile."""
    def __init__(self, filepath=constants.DOTFILE_PATH, **kwargs):
        self.filepath = filepath

    def read(self, **kwargs):
        """
        Read ``~/.pynsotrc`` and return it as a dict.
        """
        config = rcfile.rcfile(
            constants.SECTION_NAME, args={'config': self.filepath}
        )
        config.pop('config', None)  # We don't need this field in here.

        # If there is *no* config data so far and...
        if not config and not os.path.exists(self.filepath):
            p = '%s not found; would you like to create it?' % (self.filepath,)
            if click.confirm(p, default=True, abort=True):
                config_data = self.get_config_data(**kwargs)
                self.write(config_data)  # Write config to disk
                config = config_data  # Return the contents

        self.config = config

        # If we have configuration values, validate the permissions and
        # presence of fields in the dotfile.
        auth_method = config.get('auth_method')
        if auth_method == 'auth_token':
            self.validate_perms()
            required_fields = self.get_required_fields(auth_method)
            self.validate_fields(config, required_fields)

        return config

    def validate_perms(self):
        """Make sure dotfile ownership and permissions are correct."""
        if not os.path.exists(self.filepath):
            return None

        # Ownership
        s = os.stat(self.filepath)
        if s.st_uid != os.getuid():
            raise DotfileError(
                '%s: %s must be owned by you' % (
                    constants.DOTFILE_NAME, self.filepath
                )
            )

        # Permissions
        self.enforce_perms()

    def validate_fields(self, field_names, required_fields):
        """
        Make sure all the fields are set.

        :param field_names:
            List of field names to validate

        :param required_fields:
            List of required field names to check against
        """
        for rname in sorted(required_fields):
            if rname not in field_names:
                msg = '%s: Missing required field: %s' % (self.filepath, rname)
                raise DotfileError(msg)

    def enforce_perms(self, perms=constants.DOTFILE_PERMS):
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
        section = constants.SECTION_NAME
        config.add_section(section)

        # Set the config settings
        for key, val in config_data.iteritems():
            config.set(section, key, val)

        with open(filepath, 'wb') as dotfile:
            config.write(dotfile)

        self.enforce_perms()
        log.debug('wrote %s' % filepath)

    @classmethod
    def get_required_fields(cls, auth_method, required_fields=None):
        """
        Return union of all required fields for ``auth_method``.

        :param auth_method:
            Authentication method

        :param required_fields:
            Mapping of required field names to default values
        """
        if required_fields is None:
            required_fields = copy.deepcopy(constants.REQUIRED_FIELDS)

        from .client import AUTH_CLIENTS  # To avoid circular import

        # Fields that do not have default values, which are specific to an
        # auth_method.
        auth_fields = AUTH_CLIENTS[auth_method].required_arguments
        non_specific_fields = dict.fromkeys(auth_fields)
        required_fields.update(non_specific_fields)

        # Fields that MAY have default values, which are specific to an
        # auth_method, if any.
        specific_fields = constants.SPECIFIC_FIELDS.get(auth_method, {})
        required_fields.update(specific_fields)

        return required_fields

    @classmethod
    def get_config_data(cls, required_fields=None, optional_fields=None,
                        **kwargs):
        """
        Enumerate required fields and prompt for ones that weren't provided if
        they don't have default values.

        :param required_fields:
            Mapping of required field names to default values

        :param optional_fields:
            Mapping of optional field names to default values

        :param kwargs:
            Dict of prepared config settings

        :returns:
            Dict of config data
        """
        if required_fields is None:
            required_fields = constants.REQUIRED_FIELDS

        if optional_fields is None:
            optional_fields = constants.OPTIONAL_FIELDS

        config_data = {}

        # Base required fields
        cls.process_fields(config_data, required_fields, **kwargs)

        # Auth-related fields
        auth_method = config_data['auth_method']
        auth_fields = cls.get_required_fields(auth_method)
        cls.process_fields(config_data, auth_fields, **kwargs)

        # Optional fields
        cls.process_fields(
            config_data, optional_fields, optional=True, **kwargs
        )

        return config_data

    @staticmethod
    def process_fields(config_data, field_items, optional=False, **kwargs):
        """
        Enumerate fields to update ``config_data``.

        Any fields not already in ``config_data`` will be prompted for a value
        from ``field_items``.

        :param config_data:
            Dict of config data

        :param field_items:
            Dict of desired fields to be populated

        :param optional:
            Whether to consider values for ``field_items`` as optional

        :param kwargs:
            Keyword arguments of prepared values
        """
        for field, default_value in field_items.iteritems():
            prompt = 'Please enter %s' % (field,)

            # If it's already in the config data, move on.
            if field in config_data:
                continue

            # If the field was not provided
            if field not in kwargs:
                # If it does not have a default value prompt for it
                if default_value is None:
                    if not optional:
                        value = click.prompt(prompt, type=str)
                    else:
                        prompt += ' (optional)'
                        value = click.prompt(
                            prompt, default='', type=str, show_default=False
                        )

                # If the default_value is a string, prompt for it, but present
                # it as a default.
                elif isinstance(default_value, basestring):
                    value = click.prompt(
                        prompt, type=str, default=default_value
                    )

                # If it's a list of options, present the choices.
                elif isinstance(default_value, list):
                    choices = ', '.join(default_value)
                    prompt = 'Please choose %s [%s]' % (field, choices)
                    while True:
                        value = click.prompt(prompt, type=str)
                        if value not in default_value:
                            click.echo('Invalid choice: %s' % value)
                            continue
                        break
                else:
                    raise RuntimeError(
                        'Unexpected error condition when processing config '
                        'fields.'
                    )

            # Or, use the value provided in kwargs
            elif field in kwargs:
                value = kwargs[field]

            # Otherwise, use the default value
            else:
                value = default_value

            # If a value wasn't set, don't save it.
            if value == '':
                continue

            config_data[field] = value

        return config_data
