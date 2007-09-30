""" Exposes the indexer to remote invocation via pyro
"""
import logging
import time
import Pyro.core

import indexer
import pyroserver


def init():
    import logclient
    logc = logclient.LogClient()
    time.sleep(2)
    pyroserver.run_server("indexer", indexer.Indexer(log=logging.getLogger("indexer")))
    logc.stop()

if __name__ == "__main__":
    init()
