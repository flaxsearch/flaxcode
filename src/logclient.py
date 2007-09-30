""" Logging

    We read the logging configuration at startup, and then listen for
    new configurations.

"""
import logging
import logging.config
import time
import Pyro.core

class LogClient(object):
    """ gets logging configuration from the logconfserver"""

    def __init__(self):
        self.logconf = Pyro.core.getProxyForURI("PYRONAME://logconf")
        self.port = self.logconf.register()
        if not self.port:
            print "Can't start logconf client, server won't register us"
        self.listener = logging.config.listen(self.port)
        self.listener.start()
        time.sleep(1)
        self.logconf.notify_listeners([self.port])

    def __del__(self):
        self.logconf.unregister(self.port)
        logging.config.stopListening()
        self.listener.join()



