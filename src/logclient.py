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
    
    def __init__(self):
        Subscriber.__init__(self)
        self.subscribe("LogConf")

    def event(self, ev):
        update_log_config_from_string(ev.msg)

class LogListener(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(1)
    def run(self):
        Pyro.core.initServer()
        listener = LogSubscriber()
        listener.listen()

class LogQuery(object):
    """ placeholder for remote queries to the logconfserver"""

    def __init__(self):
        self.logconf = Pyro.core.getProxyForURI("PYRONAME://logconf")

    def update_log_config(self):
        update_log_config_from_string(self.logconf.get_config())

    def set_levels(self, levels):
        self.logconf.set_levels(levels)




