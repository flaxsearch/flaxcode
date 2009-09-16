import cgi

from . import get_previewer

class WSGIPreviewGen(object):

    def __init__(self):
        self.previewgen = get_previewer()


    def __call__(self, environ, start_response):
        parms = cgi.parse_qs(environ.get('QUERY_STRING'), '')
        filename = parms.get('filename')
        if filename:
            pv = self.previewgen(filename[0])
        else:
            pv = None
        start_response('200 OK', [('Content-Type', 'image/png')])
        return pv
