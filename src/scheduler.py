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
"""Schedule indexing of collections according to their configuration.

Every minute we check ask each document collection if it needs to be indexed
now. If so we call it's do_indexing method.

"""
__docformat__ = "restructuredtext en"

import datetime
import threading
import time

import flax
import util
import flaxlog

_log = flaxlog.getLogger('scheduling')

class ScheduleIndexing(util.DelayThread):

    def __init__(self,  indexserver, delay=60, **kwargs):
        util.DelayThread.__init__(self, delay, **kwargs)
        self.indexserver = indexserver

    def action(self):
        now = datetime.datetime.today()
        _log.info('Checking collections for (re-)indexing')
        for collection in flax.options.collections.itervalues():
            if collection.matching_time(now):
                _log.info('Collection: %s, due for indexing, creating request' % collection.name)
                self.indexserver.set_due(collection)
