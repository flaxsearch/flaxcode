""" Exposes the indexer to remote invocation via pyro
"""
import logging

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
    import log
    log_stopper=log.setup_logging(port=8092)
    daemon = Pyro.core.Daemon()
    ns = Pyro.naming.NameServerLocator().getNS()
    daemon.useNameServer(ns)
    name = 'indexer'
    try:
        ns.unregister(name)
    except Pyro.errors.NamingError:
        pass
    try:
        daemon.connect(IndexServer(indexer.Indexer(log=logging.getLogger("indexer"))), name)
        daemon.requestLoop()
    finally:
        log_stopper()
        daemon.shutdown(True)

if __name__ == "__main__":
    init()
