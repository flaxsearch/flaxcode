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

class FlaxRotatingFileHandler(logging.handlers.RotatingFileHandler):
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
        logging.handlers.RotatingFileHandler.__init__(self, filepath, *args)


class FlaxLazyRotatingFileHandler(FlaxRotatingFileHandler):
    """
    This class immediately closes it's stream on startup and re-opens
    it if it needs to. This is to deal with cope with a global logging
    configuration across processes where instances of this class in
    different processes refer to the same file. By using this class
    and ensuringing that only one process actually emits records to
    the handler we do away with problems I/O problems across the
    processes.
    """
    
    def __init__(self, *args):
        FlaxRotatingFileHandler.__init__(self, *args)
        if self.stream and not self.stream.closed:
            self.stream.close()

    def emit(self, *args):
        if self.stream.closed:
            self.stream = open(self.stream.name, self.stream.mode)
        FlaxRotatingFileHandler.emit(self, *args)

    def flush(self):
        if not self.stream.closed:
            FlaxRotatingFileHandler.flush(self)

    def close(self):
        if self.stream.closed:
            self.stream = open(self.stream.name, self.stream.mode)
        FlaxRotatingFileHandler.close(self)
