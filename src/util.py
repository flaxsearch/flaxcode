"""
A variety of utilities for Flax.
"""

import os
import sys
import datetime
import time
import threading
import re

def listify(obj):
    return obj if isinstance(obj, list) else [obj]


def setup_sys_path():
    "Modify sys.path in order to find libraries"
    sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'localinst')))

def setup_psyco():
    "If psyco is available ensure that it is used"
    try:
        import psyco
        psyco.background()
    except ImportError:
        pass

td_re = re.compile(r'(?P<days>\d{0,3})\s+(?P<hours>\d{0,2})\s+(?P<minutes>\d{0,2})')

def parse_timedelta(s):
    'make a timedelta from a string of the format "days hours minutes"'
    m=td_re.match(s)
    if m:
        return datetime.timedelta(days = int(m.group('days')),
                                  hours = int(m.group('hours')),
                                  minutes = int(m.group('minutes')))
    else:
        return None

def render_timedelta(td):
    'render a timedelta in the same format as that expected by parse_timedelta'
    return "%s %s %s" % (td.days, td.seconds % 3600, td.seconds % 60)


def gen_until_exception(it, ex, test):
    """ Make an iterator that yields the elements of it, and stops if
        exception ex matching predicate test is raised other
        exceptions are passed through
    """
    try:
        for x in it:
            yield x
    except ex, e:
        if test(e):
            raise StopIteration
        else:
            raise

class DelayThread(threading.Thread):
    """ A thread that runs it's action method periodically """

    def __init__(self, delay=1, **kwargs):
        threading.Thread.__init__(self, **kwargs)
        self.setDaemon(True)
        self.delay = delay

    def run(self):
        while 1:
            self.action()
            time.sleep(self.delay)

    def action(self):
        print "Subclasses should override action"

class FileWatcher(DelayThread):
    """ Watches a file for modification and notifies when such changes
        occur by calling a supplied callable.  We don't deal with
        non-existent files or cope with file deletion.
    """
    
    def __init__(self, filename, change_action,  **kwargs):
        DelayThread.__init__(self, **kwargs)
        self.filename = filename
        self.mtime = os.path.getmtime(filename)
        self.change_action = change_action

    def action(self):
        new_mtime = os.path.getmtime(self.filename)
        if new_mtime > self.mtime:
            self.mtime = new_mtime
            self.change_action()
