""" Exposes the indexer to remote invocation via pyro
"""
import logging

import Pyro.core

import indexer
import pyroserver

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
    import logclient
    logc = logclient.LogClient()
    pyroserver.run_server("indexer", IndexServer(indexer.Indexer(log=logging.getLogger("indexer"))))

if __name__ == "__main__":
    init()
