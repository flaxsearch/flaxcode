""" Logging

    We read the logging configuration at startup, and then listen for
    new configurations.

"""
import logging
import logging.config
import StringIO
import threading
import time

from Pyro.EventService.Clients import Subscriber
import Pyro.core

def update_log_config_from_string(s):
    logging.config.fileConfig(StringIO.StringIO(s))

class LogSubscriber(Subscriber):
    """ Receives logging configuration from the publisher"""
    
    def __init__(self, stop):
        Subscriber.__init__(self)
        self.subscribe("LogConf")
        self.stop=stop

    def event(self, ev):
        if self.stop.isSet():
            self.abort()
        elif ev:
            update_log_config_from_string(ev.msg)

class LogListener(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.stopper = threading.Event()
        self.stopper.clear()
        self.listener=LogSubscriber(self.stopper)

    def run(self):
        Pyro.core.initServer()
        self.listener.listen()

    def join(self, timeout = None):
        self.stopper.set()
        self.listener.event(None)
        threading.Thread.join(self, timeout)



    
    
class LogQuery(object):
    """ placeholder for remote queries to the logconfserver"""

    def __init__(self):
        self.logconf = Pyro.core.getProxyForURI("PYRONAME://logconf")

    def update_log_config(self):
        update_log_config_from_string(self.logconf.get_config())

    def set_levels(self, levels):
        self.logconf.set_levels(levels)




