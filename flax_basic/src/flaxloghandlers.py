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
"""Custom log handlers for Flax.

"""
__docformat__ = "restructuredtext en"

import logging
import logging.handlers
import os
import flaxpaths

import pkg_resources
pkg_resources.require("ConcurrentLogHandler")
import cloghandler


class FlaxRotatingFileHandler(cloghandler.ConcurrentRotatingFileHandler):
    """A rotating file handler which logs to the flax log directory.

    This is just like a standard RotatingFileHandler, except that, if the
    supplied path is a relative path, it will be located relative to the flax
    logfile directory.

    """
    def __init__(self, filename, *args):
        if os.path.isabs(filename):
            filepath = filename
        else:
            filepath = os.path.join(flaxpaths.paths.log_dir, filename)
        cloghandler.ConcurrentRotatingFileHandler.__init__(self, filepath, *args)
