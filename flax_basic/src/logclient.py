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

import cStringIO
import ConfigParser
import logging
import logging.handlers
import logging.config
import multiprocessing
import urllib

import util
import flaxpaths

def read_client_logconf():
    logging.config.fileConfig(flaxpaths.paths.logclientconf_path)


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
            logging.config.fileConfig(self.filepath)
            

class LogConfPub(object):
    """
    Watches the file named by `filepath` for changes, and posts
    its contents to `url` when it changes.

    If url is not provided use the client logging configuration to
    figure out the url.
    
    """
    def __init__(self, filepath, url=None):
        self.filepath = filepath
        if url is None:
            self.url = self.url_from_client_conf()
        else:
            self.url = url

    def publish_new_file(self):
        data = cStringIO.StringIO()
        logdir = flaxpaths.paths.log_dir
        if logdir[-1] != '/':
            logdir = logdir + '/'
        logdir = "'" + logdir + "'"
        parser = ConfigParser.SafeConfigParser(
            defaults={'logdir': logdir})
        parser.read(flaxpaths.paths.logconf_path)
        parser.write(data)
        urllib.urlopen(self.url, data=data.getvalue())

    def url_from_client_conf(self):
        parser = ConfigParser.SafeConfigParser()
        parser.read(flaxpaths.paths.logclientconf_path)
        args = parser.get('handler_mainhandler', 'args')
        # looks like a potential security hole, but the logging module
        # does this anyway so we're no doing anthing that's not
        # already done by using logging.config.fileConfig. USers
        # should ensure that the config file is secure.
        args = eval(args)
        host = args[0]
        path = args[1]
        #path includes the log url, so should strip that off
        logpos = path.find('log')      
        url = "http://" + host + path[:logpos] + 'config'
        return url
    
def initialise_logging():
    # all log requests get sent - we don't want things to be filtered
    # locally because it's the configuration at the log server's end
    # that counts.
    read_client_logconf()

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
        read_client_logconf()
