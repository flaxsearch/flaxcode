import Pyro.core
import Pyro.naming

def run_server(name, server):
    daemon = Pyro.core.Daemon()
    ns = Pyro.naming.NameServerLocator().getNS()
    daemon.useNameServer(ns)
    try:
        ns.unregister(name)
    except Pyro.errors.NamingError:
        pass
    try:
        daemon.connect(server, name)
        daemon.requestLoop()
    finally:
        daemon.shutdown(True)
