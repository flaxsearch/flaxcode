from __future__ import with_statement

import Pyro.EventService.Clients
import filewatch

class LogConfPub(Pyro.EventService.Clients.Publisher):

    def __init__(self, filename):
        Pyro.EventService.Clients.Publisher.__init__(self)
        self.filename = filename
        filewatch.FileWatcher(self.filename, self.publish_new_file).start()

    def publish_new_file(self):
        with open(self.filename) as f:
            self.publish("LogConf", f.read())
