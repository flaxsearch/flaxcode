#
# copyright 2006/2007 Lemur Consulting Limited. All rights reserved.
#

import os, os.path
import cherrypy

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

        return "[[%s, 'fixme', true], [%s, 'wibble', false]]" % (
            repr(os.path.join(fpath, 'fixme')), 
            repr(os.path.join(fpath, 'wibble')))

config = {
    'global': {
        'server.socket_port' : 8010,
        'server.logToScreen' : True,
    },
    '/static': {
        'tools.staticdir.on'  : True,
        'tools.staticdir.dir' : '/Users/maky/src/flaxcode/filebrowser/static/'
    }}

cherrypy.config.update(config)
cherrypy.tree.mount(BrowserServer(), '/', config=config)
cherrypy.server.quickstart()
cherrypy.engine.start()
