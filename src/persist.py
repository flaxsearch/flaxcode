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
    d = shelve.open(filename)
    d['flax'] = options
    d.close()

def read_flax(filename):
    d = shelve.open(filename)
    try:
        options = d['flax']
        if options.version != flax.current_version:
            log=logging.getLogger().warn("The version of %s is incompatible, reverting to default settings" % filename)
            options = flax.make_options()
    except (KeyError, AttributeError):
        log=logging.getLogger().warn("There was a problem reading %s, reverting to default settings" % filename)
        options = flax.make_options()
    d.close()
    return options

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
