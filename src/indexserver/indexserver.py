""" Exposes the indexer to remote invocation via pyro
"""
import logging
import indexer
import util

def init():
    import logclient
    logclient.LogListener().start()
    logclient.LogQuery().update_log_config()
    util.run_server("indexer", indexer.Indexer())

if __name__ == "__main__":
    init()
