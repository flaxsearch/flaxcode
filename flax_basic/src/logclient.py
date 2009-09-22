# Copyright (C) 2007, 2008, 2009 Lemur Consulting Ltd
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
"""Support for logging.

We read the logging configuration at startup, and then listen for new
configurations.

"""
from __future__ import with_statement
__docformat__ = "restructuredtext en"

import ConfigParser
import logging
import logging.handlers
import multiprocessing
import urllib

import util
import flaxpaths

class LogConf(object):
    """ Simple log configuration control/querying.

    """
    def __init__(self, filepath):
        self.filepath = filepath
        self.parser = ConfigParser.SafeConfigParser()

    #FIXME - refactor common parts of get_levels and set_levels
    def get_levels(self, level_names):
        """
        Return a dictionary whose keys are the `logger_names`
        and whose values are their levels.

        """
        self.parser.read(self.filepath)
        rv = {}
        for name in level_names:
            if name == "":
                name = "root"
            sec_name = 'logger_%s' % name.replace('.','_')
            level = self.parser.get(sec_name, 'level')
            rv[name] = level
        return rv
    
    def set_levels(self, logger_levels):
        """
        logger_levels is a sequence of (logger, level) pairs, where
        logger is a string naming a logger and level is a number.  If
        the new levels are different from the current one the write
        the configuration to self.filepath.
        
        """
        self.parser.read(self.filepath)
        changed = False
        for logger, level in logger_levels.iteritems():
            if logger == "":
                logger = "root"
            sec_name = 'logger_%s' % logger.replace('.','_')
            current_level = self.parser.get(sec_name, 'level')
            if level != current_level:
                self.parser.set(sec_name, 'level', level)
                changed = True
        if changed:
            with open(self.filepath, 'w') as f:
                self.parser.write(f)

class LogConfPub(object):
    """
    Watches the file named by `filepath` for changes, and posts
    its contents to `url` when it changes.
    
    """
    def __init__(self, filepath, url):
        self.filepath = filepath
        self.url = url
        util.FileWatcher(self.filepath, self.publish_new_file).start()

    def publish_new_file(self):
        with open(self.filepath) as f:
            urllib.urlopen(self.url, data=f.read())

class FlaxHTTPHandler(logging.handlers.HTTPHandler):

    def emit(self, msg):
        logging.handlers.HTTPHandler.emit(self, msg)

def initialise_logging(host, url):
    # all log requests get sent - we don't want things to be filtered
    # locally because it's the configuration at the log server's end
    # that counts.
    root_logger = logging.getLogger()
    root_logger.level = 0
    handler = FlaxHTTPHandler(host, url, 'POST')
    handler.level = 0
    root_logger.addHandler(handler)

class LogClientProcess(multiprocessing.Process):
    """
    A processing.Process configuration so that logging calls are
    handled by posting to the web location given by `host` and
    `url`. Subclass run implementations should call initialise_logging
    before doing their main work.

    """

    def __init__(self, *args, **kwargs):
        super(LogClientProcess, self).__init__(*args, **kwargs)
        self.flaxpaths = flaxpaths.paths
        
    def initialise_logging(self):
        flaxpaths.paths = self.flaxpaths
        initialise_logging(self.flaxpaths.logging_host,
                           self.flaxpaths.logging_path)
