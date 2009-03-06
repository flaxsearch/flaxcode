# Copyright (C) 2007 Lemur Consulting Ltd
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""Authentication values used by Flax.

"""
__docformat__ = "restructuredtext en"

import ConfigParser
import md5
import os

import flaxpaths

def encrypt_password(password):
    """Convert a password to the encrypted form.

    """
    return md5.new(password).hexdigest()

class FlaxAuth(object):
    """Authentication values used by Flax.

    This is a singleton class.

    This stores a dictionary of username/password values.  Currently, no extra
    information is stored for each username - for now, all users with passwords
    are administrators.

    """
    def __new__(cls, *args, **kwargs):
        """Ensure that there is only one instance of the object.

        """
        if not '_the_instance' in cls.__dict__:
            cls._the_instance = object.__new__(cls)
        return cls._the_instance

    def __init__(self):
        """Initialise the empty list of authentication tokens.

        """
        # Dictionary, keyed by user, with the (encrypted) password as the
        # value.
        self._userpass = {}

    def load(self, conf_path):
        """Load the authentication tokens from a file.

        First drops all the currently loaded authentication tokens.

        """
        self._userpass = {}
        config = ConfigParser.ConfigParser()
        files_read = config.read(conf_path)
        if len(files_read) != 1 or files_read[0] != conf_path:
            raise ValueError("Couldn't read authentication configuration file '%s'"
                             % conf_path)

        if not config.has_section('passwords'):
            raise ValueError("Authentication configuration file '%s' has no 'passwords' section"
                             % conf_path)

        for user in config.options('passwords'):
            password = config.get('passwords', user, raw=True)
            self._userpass[user] = password

    def save(self, conf_path):
        """Save the authentication tokens to a file.

        """
        conf_path_tmp = conf_path + '.tmp'
        config = ConfigParser.ConfigParser()
        config.add_section('passwords')
        for user, password in self._userpass.iteritems():
            config.set('passwords', user, password)
        fd = open(conf_path_tmp, 'wb')
        try:
            try:
                config.write(fd)
            finally:
                fd.close()
            if os.path.exists(conf_path):
                os.unlink(conf_path)
            os.rename(conf_path_tmp, conf_path)
        except:
            if os.path.exists(conf_path_tmp):
                os.unlink(conf_path_tmp)
            raise

    def set(self, username, password):
        """Set the password for a given username.

        The supplied password should not be encrypted.

        """
        self._userpass[username] = encrypt_password(password)

    def get_as_dict(self):
        """Get as a dictionary from username to encrypted passwords.

        """
        return self._userpass

# The single, global, instance of FlaxAuth.
_auth = FlaxAuth()

def load():
    """Load the authentication tokens from the configuration file.

    """
    _auth.load(flaxpaths.paths.authconf_path)

def save():
    """Save the authentication tokens to the configuration file.

    """
    _auth.save(flaxpaths.paths.authconf_path)

set = _auth.set
get_as_dict = _auth.get_as_dict
