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

    The directory paths stored in this module are:

     - src_dir: the directory where our source files are
     - dbs_dir: the parent directory under which databases are created.
     - log_dir: the directory in which logs are stored.
     - conf_dir: the directory in which configuration files are stored.
     - var_dir: the directory in which persistent runtime state is stored.

    """
    def __new__(cls, *args, **kwargs):
        """Ensure that there is only one instance of the object.

        """
        if not '_the_instance' in cls.__dict__:
            cls._the_instance = object.__new__(cls)
        return cls._the_instance

    def set_dirs(self, main_dir=None, src_dir=None,
                 dbs_dir=None, log_dir=None, conf_dir=None, var_dir=None):
        """Set the directories for Flax to use.

         - main_dir: Only required if any of the more specific directories are
           not specified - specifies a top-level directory under which all the
           files will be placed.
         - dbs_dir: the parent directory under which databases are created.
         - log_dir: the directory in which logs are stored.
         - conf_dir: the directory in which configuration files are stored.
         - var_dir: the directory in which persistent runtime state is stored.

        """
        self.src_dir = src_dir if src_dir else os.path.dirname(__file__)
        self.dbs_dir = dbs_dir
        self.log_dir = log_dir
        self.conf_dir = conf_dir
        self.var_dir = var_dir

        if self.dbs_dir is None or \
           self.log_dir is None or \
           self.conf_dir is None or \
           self.var_dir is None:
            if main_dir is None:
                raise ValueError("main_dir must be specified unless all "
                                 "specific configuration directories are.")

        if self.src_dir is None:
            self.src_dir = main_dir
        if self.dbs_dir is None:
            self.dbs_dir = os.path.join(main_dir, 'dbs')
        if self.log_dir is None:
            self.log_dir = os.path.join(main_dir, 'logs')
        if self.conf_dir is None:
            self.conf_dir = os.path.join(main_dir, 'conf')
        if self.var_dir is None:
            self.var_dir = os.path.join(main_dir, 'var')

    def makedirs(self):
        """Create the directories used by flax.

        """
        if not os.path.exists(self.dbs_dir):
            os.makedirs(self.dbs_dir)
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        if not os.path.exists(self.conf_dir):
            os.makedirs(self.conf_dir)
        if not os.path.exists(self.var_dir):
            os.makedirs(self.var_dir)

    @property
    def logconf_path(self):
        """The path of the logging configuration file.

        """
        return os.path.join(self.conf_dir, 'flaxlog.conf')

    @property
    def cpconf_path(self):
        """The path of the cherrypy configuration file.

        """
        return os.path.join(self.conf_dir, 'cp.conf')

    @property
    def authconf_path(self):
        """The path of the cherrypy password file.

        """
        return os.path.join(self.conf_dir, 'auth.conf')

    @property
    def templates_path(self):
        """The path of the template directory.

        """
        return os.path.join(self.src_dir, 'templates')

    @property
    def flaxstate_path(self):
        """The path of the main file holding the current flax state.

        """
        return os.path.join(self.var_dir, 'flax.flx')

    @property
    def static_dir(self):
        """The path of the static files to serve to the webserver.

        """
        return os.path.join(self.src_dir, 'static')

paths = FlaxPaths()


# so that we can use this in tests. In startflax.py set_dirs is called
# again with arguments taken from the command line.
this_dir = os.path.dirname(os.path.realpath(__file__))
paths.set_dirs(conf_dir=this_dir,
               main_dir=os.path.join(this_dir, 'data'))

