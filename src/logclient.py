""" Logging

    We read the logging configuration at startup, and then listen for
    new configurations.

"""
import logging
import logging.config
import StringIO
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

class LogQuery(object):
    """ placeholder for remote queries to the logconfserver"""

    def __init__(self):
        self.logconf = Pyro.core.getProxyForURI("PYRONAME://logconf")

    def update_log_config(self):
        update_log_config_from_string(self.logconf.get_config())

    def set_levels(self, levels):
        self.logconf.set_levels(levels)




