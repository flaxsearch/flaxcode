import Pyro.core
import Pyro.naming

import util

def run_server(name, server, shutdown_actions=None):
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
        while 1:
            daemon.handleRequests(3)
    except KeyboardInterrupt:
        print "Finishing"
        if shutdown_actions:
            shutdown_actions()
    finally:
        daemon.shutdown(True)
