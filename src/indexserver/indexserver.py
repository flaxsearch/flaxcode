""" Exposes the indexer to remote invocation via pyro
"""
import logging
import time
import Pyro.core

import indexer
import pyroserver


def init():
    import logclient
    log_subscriber = logclient.LogListener()
    log_query = logclient.LogQuery()
    log_query.update_log_config()
    pyroserver.run_server("indexer", indexer.Indexer())

if __name__ == "__main__":
    init()
