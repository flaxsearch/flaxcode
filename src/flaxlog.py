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
"""New logging module.

Simplified logging for Flax. This uses the standard logging module, but hides it for client
code (as the standard framework gets confused by multiple processes.)  Client code should import
flaxlog and then call 

    flaxlog.debug('indexing', 'we indexed a file', *args, **kwargs)
    
Where 'indexing' is the name of the log category (we anticipate 'indexing', 'searching' and 
'other'.)  These are implemented as separate loggers.
"""

from __future__ import with_statement
__docformat__ = "restructuredtext en"

import logging
import Queue
import processing

import time
import os

_q = processing.Queue()

def update_conf(conf):
    # put config object onto queue!!!  It will get through soon enough.
    pass

class _Logger:
    def __init__(self, name, q):
        self._name = name
        self._q = q

    def debug(self, msg, *args, **kwargs):
        self.log(logging.DEBUG, msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self.log(logging.INFO, msg, *args, **kwargs)

    def warn(self, msg, *args, **kwargs):
        self.log(logging.WARNING, msg, *args, **kwargs)

    warning = warn

    def error(self, msg, *args, **kwargs):
        self.log(logging.ERROR, msg, *args, **kwargs)

    def critical(self, logger, msg, *args, **kwargs):
        self.log(logging.CRITICAL, msg, *args, **kwargs)

    def log(self, level, msg, *args, **kwargs):
        self._q.put((level, self._name, msg, args, kwargs))

def getLogger(name):
    return _Logger(name, _q)
    
def close():
    _q.put(None)
    
class LoggerProc(processing.Process):
    """Separate process handles logging for whole app.
    
    Takes items from the queue and logs them.
    """
    
    def run(self):
        self.loggers = {}
        self.handler = logging.StreamHandler()  # FIXME
        self.handler.setFormatter(logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s'))

        while True:
            o = _q.get(True)     # blocks until available
            if o is None: return
            self.get_logger(o[1]).log(o[0], o[2], *o[3], **o[4])

    def get_logger(self, name):
        try:
            return self.loggers[name]
        except KeyError:
            l = logging.getLogger(name)
            l.setLevel(logging.DEBUG)  # FIXME should depend on logger
            l.addHandler(self.handler)
            self.loggers[name] = l
            return l

# start logger thread when module is loaded
LoggerProc().start()

if __name__ == '__main__':
    class TestProc(processing.Process):
        def run(self):
            getLogger('foo').debug('from pid %s' % os.getpid())

    TestProc().start()
    TestProc().start()
    TestProc().start()
    time.sleep(1)        # let the testprocs start
    close()
    