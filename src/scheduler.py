""" Index Document collections when the necessary.

    Every minute we check ask each document collection if it needs to
    be indexed now. If so we call it's do_indexing method
    
"""

import util
import datetime
import flax

class ScheduleIndexing(util.StoppingThread):

    def action(self):
        now = datetime.datetime.today()
        for collection in flax.options.collections.itervalues():
            if collection.matching_time(now):
                collection.do_indexing(flax.options.filter_settings)

