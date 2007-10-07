""" Index Document collections when the necessary.

    Every minute we check ask each document collection if it needs to
    be indexed now. If so we call it's do_indexing method
    
"""

import datetime
import threading
import time

import flax
import util
import logging


class ScheduleIndexing(util.DelayThread):

    def __init__(self,  indexserver, delay=60, **kwargs):
        util.DelayThread.__init__(self, delay, **kwargs)
        self.log = logging.getLogger('scheduling')
        self.indexserver = indexserver

    def action(self):
        now = datetime.datetime.today()
        self.log.info('Checking collections for (re-)indexing')
        for collection in flax.options.collections.itervalues():
            if collection.matching_time(now):
                self.log.info('Collection: %s, due for indexing, creating request' % collection.name)
                self.indexserver.do_indexing(collection, flax.options.filter_settings)

