from __future__ import with_statement
import collections
import socket
import struct
import re
import threading
import ConfigParser
import filewatch


class LogConf(object):
    """ Simple logconfiguration control/querying
    """
    
    def __init__(self, filename):

        self.filename = filename
        self.parser = ConfigParser.SafeConfigParser()

    def get_config(self):
        with open(self.filename) as f:
            return f.read()


    
    def set_levels(self, logger_levels):
        """
        logger_levels is a sequence of (logger, level) pairs,
        where logger is a string naming a logger and level is a number
        """
        self.parser.read(self.logconf_file)
        changed = False
        for logger, level in logger_levels:
            sec_name = 'logger_%s' % logger
            current_level = int(sec_name, 'level')
            if level != current_level:
                self.parser.set(secname, 'level', level)
                changed = True
        if changed:
            with open(self.logconf_file, 'w') as f:
                self.parser.write(f)


