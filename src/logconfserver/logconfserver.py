import Pyro
import logconf

import sys
sys.path.append('..')
import pyroserver

class LogConfServer(Pyro.core.ObjBase):

    def __init__(self, logconf):
        Pyro.core.ObjBase.__init__(self)
        self.logconf=logconf

    def register(self, *args, **kwargs):
        return self.logconf.register(*args, **kwargs)

    def unregister(self, *args, **kwargs):
        return self.logconf.unregister(*args, **kwargs)
        
    def notify_listeners(self, *args, **kwargs):
        return self.logconf.notify_listeners(*args, **kwargs)

    def set_level(self, *args, **kwargs):
        return self.logconf.set_level(*args, **kwargs)

def init():
    pyroserver.run_server("logconf", LogConfServer(logconf.LogConf('flaxlog.conf', [8091, 8092, 8093, 8094])))

if __name__ == "__main__":
    init()
