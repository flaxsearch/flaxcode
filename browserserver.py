#
# copyright 2006/2007 Lemur Consulting Limited. All rights reserved.
#

import platform
import sys
import os, os.path
import cherrypy
import string

_is_windows = platform.system() == 'Windows'
if _is_windows:
    import win32api
    
class BrowserServer (object):
    @cherrypy.expose
    def listfiles(self, fpath=''):
        """List files in fpath (assuming it is a directory).
        
        Returns a JSON list:
        
        [[filepath, filename, is-dir, is-readable], ...]

        """
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        # prevent IE caching
        cherrypy.response.headers['Expires'] = 'Mon, 26 Jul 1997 05:00:00 GMT'

        print '--', fpath
        if fpath:
            ret = []
            for f in os.listdir(fpath):
                fp = os.path.join(fpath, f).replace('\\', '/')
                canread = int(os.access(fp, os.R_OK))
                if os.path.isdir(fp):
                    ret.append ([fp, f + os.path.sep, 1, canread])
                else:
                    ret.append ([fp, f, 0, canread])
            
            return repr(ret)
        
        else:
            # special case - return list of filesystem roots
            if _is_windows:
                drives = win32api.GetLogicalDriveStrings()
                drives = string.splitfields(drives,'\000')
                drives = [[d.replace('\\', '/'), d, 1, 1] for d in drives if d]
                print '-- drives:', drives
                return repr(drives)
            else:
                return "[['/', '/', 1, 1]]"                

config = {
    'global': {
        'server.socket_port' : 8010,
        'server.logToScreen' : True,
    },
    '/static': {
        'tools.staticdir.on'  : True,
        'tools.staticdir.dir' : os.path.abspath('static')
    }}

cherrypy.config.update(config)
cherrypy.tree.mount(BrowserServer(), '/', config=config)
cherrypy.server.quickstart()
cherrypy.engine.start()
