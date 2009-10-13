import ConfigParser

import setuppaths
import flaxpaths
import logserver

def run():
    parser = ConfigParser.SafeConfigParser()
    parser.read(flaxpaths.paths.cpconf_path)
    flaxport = parser.getint('global', 'server.socket_port')
    logserverconf = {
        'global': {
            'server.socket_port' : flaxport+1,
            'engine.autoreload_on' : False,
            'blocking': True
            }
        }
    logserver.start_log_server(logserverconf)

if __name__ == "__main__":
    run()
