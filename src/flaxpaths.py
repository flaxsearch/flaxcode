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
"""File paths used by Flax.

"""
__docformat__ = "restructuredtext en"

import os

class FlaxPaths(object):
    """Paths used by Flax.

    This is a singleton class.

    """
    def __new__(cls, *args, **kwargs):
        """Ensure that there is only one instance of the object.

        """
        if not '_the_instance' in cls.__dict__:
            cls._the_instance = object.__new__(cls)
        return cls._the_instance

    def __init__(self):
        self.src_dir = os.path.dirname(__file__)

    def set_dirs(self, main_dir=None,
                 dbs_dir=None, log_dir=None, conf_dir=None):
        """Set the directories for Flax to use.

        """
        self.dbs_dir = dbs_dir
        self.log_dir = log_dir
        self.conf_dir = conf_dir

        if self.dbs_dir is None or \
           self.log_dir is None or \
           self.conf_dir is None:
            if main_dir is None:
                raise ValueError("main_dir must be specified unless all "
                                 "specific configuration directories are.")

        if self.dbs_dir is None:
            self.dbs_dir = os.path.join(main_dir, 'dbs')
        if self.log_dir is None:
            self.log_dir = os.path.join(main_dir, 'logs')
        if self.conf_dir is None:
            self.conf_dir = srcdir

    def makedirs(self):
        """Create the directories used by flax.

        """
        if not os.path.exists(self.dbs_dir):
            os.makedirs(self.dbs_dir)
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        if not os.path.exists(self.conf_dir):
            os.makedirs(self.conf_dir)

    @property
    def logconf_path(self):
        """The path of the logging configuration file.

        """
        return os.path.join(self.conf_dir, 'flaxlog.conf')

    @property
    def cpconf_path(self):
        """The path of the cherrypy configuration file

        """
        return os.path.join(self.conf_dir, 'cp.conf')

    @property
    def staticdir(self):
        """The path of the static files to serve to the webserver.

        """
        return os.path.join(self.src_dir, 'static')

paths = FlaxPaths()
