#
# copyright 2006/2007 Lemur Consulting Limited. All rights reserved.
#

import platform
import os, os.path
import cherrypy

_is_windows = platform.system() == 'Windows'

class BrowserServer (object):
    @cherrypy.expose
    def listfiles(self, fpath=''):
        """List files in fpath (assuming it is a directory).
        
        Returns a JSON list:
        
        [[filepath, filename, is-dir], ...]

        """
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        # prevent IE caching
        cherrypy.response.headers['Expires'] = 'Mon, 26 Jul 1997 05:00:00 GMT'

        if fpath:
            ret = []
            for f in os.listdir(fpath):
                fp = os.path.join(fpath, f)
                if os.access(fp, os.R_OK):
                    if os.path.isdir(fp):
                        ret.append ([fp, f + os.path.sep, 1])
                    else:
                        ret.append ([fp, f, 0])
            
            return repr(ret)
        
        else:
            # special case - return list of filesystem roots
            if _is_windows:
                return "[['C:\\\\', 'C:\\\\', true], ['FIXME', 'FIXME', false]]"
                # FIXME - get list of drive letters and network shares, using
                # win32api and win32com
            else:
                return "[['/', '/', true]]"                

config = {
    'global': {
        'server.socket_port' : 8010,
        'server.logToScreen' : True,
    },
    '/static': {
        'tools.staticdir.on'  : True,
        'tools.staticdir.dir' : '/Users/maky/src/flax/branches/filebrowser/static/'
    }}

cherrypy.config.update(config)
cherrypy.tree.mount(BrowserServer(), '/', config=config)
cherrypy.server.quickstart()
cherrypy.engine.start()
