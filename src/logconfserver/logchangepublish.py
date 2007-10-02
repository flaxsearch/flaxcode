from __future__ import with_statement

import threading
import Pyro.EventService.Clients

import filewatch

class LogConfPub(Pyro.EventService.Clients.Publisher):

    def __init__(self, filename):
        Pyro.EventService.Clients.Publisher.__init__(self)
        self.filename = filename
        self.stopper = threading.Event()
        self.stopper.clear()
        self.filewatch=filewatch.FileWatcher(self.stopper, self.filename, self.publish_new_file)
        self.filewatch.start()

    def stop(self):
        self.stopper.set()
        self.filewatch.join()

    def publish_new_file(self):
        with open(self.filename) as f:
            self.publish("LogConf", f.read())
