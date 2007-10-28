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
"""Support for logging.

We read the logging configuration at startup, and then listen for new
configurations.

"""
from __future__ import with_statement
__docformat__ = "restructuredtext en"

import ConfigParser
import logging
import logging.config
import flaxloghandlers
import StringIO
import threading
import processing
import time

import util

# Add flaxloghandlers to the logging module, to make it available from the
# log configuration file.
logging.flaxloghandlers = flaxloghandlers

def update_log_config_from_string(s):
    logging.config.fileConfig(StringIO.StringIO(s))

class LogListener(threading.Thread):
    def __init__(self, inpipe):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.inpipe=inpipe

    def run(self):
        while 1:
            new_log = self.inpipe.recv()
            update_log_config_from_string(new_log)


class LogConf(object):
    """ Simple log configuration control/querying.

    """
    def __init__(self, filepath):
        self.filepath = filepath
        self.parser = ConfigParser.SafeConfigParser()

    def update_log_config(self):
        with open(self.filepath) as f:
            update_log_config_from_string(f.read())

    def set_levels(self, logger_levels):
        """
        logger_levels is a sequence of (logger, level) pairs,
        where logger is a string naming a logger and level is a number
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
    """ Publishes changes in the file named by `filepath` to all the
    objects in subscribers. These must have a .send method which will
    be called to send the new file contents to them.
    """
    def __init__(self, filepath, subscribers):
        self.filepath = filepath
        self.subscribers = subscribers
        util.FileWatcher(self.filepath, self.publish_new_file).start()

    def publish_new_file(self):
        with open(self.filepath) as f:
            data = f.read()
            for s in self.subscribers:
                s.send(data)
