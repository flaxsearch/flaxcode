import Pyro
import logconf
import logchangepublish
import sys
sys.path.append('..')
import pyroserver

def init():
    filename = 'flaxlog.conf'

    pub = logchangepublish.LogConfPub(filename)

    svr = logconf.LogConf(filename)
    pyroserver.run_server("logconf", svr)


if __name__ == "__main__":
    init()
