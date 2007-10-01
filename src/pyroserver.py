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
