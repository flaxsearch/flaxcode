""" Exposes the indexer to remote invocation via pyro
"""
import logging
import time
import Pyro.core

import indexer
import util

def init():
    import logclient
    log_listener = logclient.LogListener()
    logclient.LogQuery().update_log_config()
    util.run_server("indexer", indexer.Indexer(), util.join_all_threads)



if __name__ == "__main__":
    init()
