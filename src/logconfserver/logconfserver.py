import Pyro
import logconf

import sys
sys.path.append('..')
import pyroserver

def init():
    svr = logconf.LogConf('flaxlog.conf', [8091, 8092, 8093, 8094])
    pyroserver.run_server("logconf", svr)
    del(svr)

if __name__ == "__main__":
    init()
