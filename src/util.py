"""
A variety of utilities for Flax.
"""

import os
import sys
import datetime
import time
import threading
import re

def setup_sys_path():
    "Modify sys.path in order to find libraries"
    sys.path.insert(0, os.path.normpath(os.path.join(__file__, '..', '..', 'libs', 'xappy')))
    sys.path.insert(0, os.path.normpath(os.path.join(__file__, '..', '..', 'libs')))

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

import Pyro.core
import Pyro.naming

def run_server(name, server):
    remoting_server = Pyro.core.ObjBase()
    remoting_server.delegateTo(server)
    Pyro.core.initServer()
    daemon = Pyro.core.Daemon()
    ns = Pyro.naming.NameServerLocator().getNS()
    daemon.useNameServer(ns)
    try:
        ns.unregister(name)
    except Pyro.errors.NamingError:
        pass

    daemon.connect(remoting_server, name)
    try:
        daemon.requestLoop()
    finally:
        daemon.shutdown(True)

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

import cPickle as pickle

class IO(object):
    """
    A utility class to aid communication between processes.
    
    Simple communication based on file like objects for sending and
    recieving data and using pickle to serialize python objects.
    """

    def __init__(self, instream = sys.stdin, outstream = sys.stdout, pickle_protocol = -1):
        self.instream = instream
        self.outstream = outstream
        self.pickle_protocol = pickle_protocol
    
    def receive(self):
        return pickle.load(self.instream)

    def send(self, obj):
        pickle.dump(obj, self.outstream, self.pickle_protocol)
