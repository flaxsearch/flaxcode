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
"""Persistence for configuration settings.

"""
from __future__ import with_statement
__docformat__ = "restructuredtext en"

import logging
import shelve
import threading
import time
import flax
import util

def store_flax(filename, options):
    """Store the flax options.

    :Parameters:
     - `filename`: The filename to read the options from.
     - `options`: The FlaxOptions object to write the options to.

    If the options are not yet initialised, nothing will be stored.

    """
    logging.getLogger().debug("Storing flax options")
    if not options.initialised():
        # Options weren't initialised - don't store anything.
        return
    options_dict = options.to_dict()
    logging.getLogger().debug("Storing options: %r" % options_dict)

    d = shelve.open(filename)
    d['flax'] = options_dict
    d.close()

def read_flax(filename, options):
    """Read the flax options.

    :Parameters:
     - `filename`: The filename to read the options from.
     - `options`: The FlaxOptions object to write the options to.

    If the file is invalid in any way, the options will be set to default
    values.

    """
    d = shelve.open(filename)
    try:
        options_dict = d['flax']
        logging.getLogger().debug("Got options: %r" % options_dict)
        options_version = options_dict.get('version', None)
        if options_version != flax.current_version:
            logging.getLogger().warn("The version of %s is incompatible, reverting to default settings" % filename)
            options.set_to_defaults()
            data_changed.set()
        else:
            options.from_dict(options_dict)
    except (KeyError, AttributeError):
        logging.getLogger().warn("There was a problem reading %s, reverting to default settings" % filename)
        options.set_to_defaults()
        data_changed.set()
    d.close()

data_changed = threading.Event()
data_changed.clear()

class DataSaver(util.DelayThread):
    """ thread to periodically save data """

    def __init__(self, filename, **kwargs):
        self.filename=filename
        util.DelayThread.__init__(self, **kwargs)

    def action(self):
        if data_changed.isSet():
            store_flax(self.filename, flax.options)
            data_changed.clear()
