import Pyro
import logconf
import logchangepublish
import sys
sys.path.append('..')
import util

def init():
    filename = 'flaxlog.conf'
    lcp = logchangepublish.LogConfPub(filename)
    util.run_server("logconf", logconf.LogConf(filename))
    

if __name__ == "__main__":
    init()
