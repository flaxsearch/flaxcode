""" Exposes the indexer to remote invocation via pyro
"""

import Pyro.core
import Pyro.naming

import indexer

class IndexServer(Pyro.core.ObjBase):

    def __init__(self, indexer):
        """ Initialize the index server. indexer must be a class that
        has a method named do_indexing.
        """
        Pyro.core.ObjBase.__init__(self)
        self.indexer = indexer

    def do_indexing(self, *args, **kwargs):
        self.indexer.do_indexing(*args, **kwargs)


def init():
    daemon = Pyro.core.Daemon()
    ns = Pyro.naming.NameServerLocator().getNS()
    daemon.useNameServer(ns)
    name = 'indexer'
    try:
        ns.unregister(name)
    except Pyro.errors.NamingError:
        pass
    try:
        daemon.connect(IndexServer(indexer.Indexer()), name)
        daemon.requestLoop()
    finally:
        daemon.shutdown(True)

if __name__ == "__main__":
    init()
