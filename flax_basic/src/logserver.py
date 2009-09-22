# Copyright (C) 2009 Lemur Consulting Ltd
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

# Some portions of this code are based on examples in the python
# documentation. Copyright (C) 1990-2009, Python Software Foundation.

import os
import cgi
import logging
import logging.config
import logging.handlers
import flaxloghandlers
import multiprocessing
import StringIO
import re
import urlparse
import wsgiref
import wsgiref.simple_server

class WSGILoggingApp(object):
    """
    This application provides a web interface to the python logging
    infrastructure.

    It is intended as one way of using the logging system in
    multiprocess applications, where propagation of configuration
    information, and contention for things like logging output file is
    problematic.

    Note that the application potentially modifies the global logging
    configuration for the process that it is running in. If the
    webserver that mounts this application uses the python logging
    system care will be needed with the naming of loggers to ensure
    that the web server's own logging is not disrupted.

    Two different urls are served. Posting to 'log' causes a logrecord
    to be propogated according to the current logging
    configuration. Posting to 'config' changes the logging
    configuration. Getting from 'config' returns the current logging
    configuration.

    """

    def __init__(self):
        urls = (
            (r'log/?$', self.log),
            (r'log/(.+)$', self.log),
            (r'config/?$', self.config),
            (r'config/(.+)$', self.config),
            )
        self.urls = [(re.compile(r), f) for r, f in urls]
    
    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '').lstrip('/')
        for r, func in self.urls:
            match = r.search(path)
            if match is not None:
                environ['logger.url_args'] = match.groups()
                return func(environ, start_response)
        return self.not_found(environ, start_response)

    def not_found(self, environ, start_response):
        start_response('404 NOT FOUND', [('Content-Type', 'text/plain')])
        return ['Not Found']

    arg_adapters = { 'args' : (lambda x : (() if x == '()' else x)),
                     'exc_info': (lambda x: (None if x == 'None' else x)),
                     'exc_text': (lambda x: (None if x == 'None' else x)),
                     'created' : float,
                     'msecs' : float,
                     'relativeCreated': float,
                     'levelno': int,
                     'thread' : int,
                     'process': int,
                     'lineno': int}

    def log(self, environ, start_response):
        method = environ.get('REQUEST_METHOD', '')
        if method == 'POST':
            start_response("200 OK", [('Content-type', 'text/plain')])
            args = dict(
                urlparse.parse_qsl(
                    environ['wsgi.input'].read(int(environ.get('CONTENT_LENGTH',0))),
                    keep_blank_values=True))
            for key in args:
                if key in self.arg_adapters:
                    args[key] = self.arg_adapters[key](args[key])
            record = logging.makeLogRecord(args)
            logger = logging.getLogger(record.name)
            if logger.isEnabledFor(record.levelno):
                logger.handle(record)
            return "Record Processed"
        else:
            start_response("405 Method not Allowed",
                           [('Content-type', 'text/plain')])
            return "Only POSTing to this resource is supported"


    def config(self, environ, start_response):
        method = environ.get('REQUEST_METHOD', '')
        if method == 'POST':
            length = int(environ.get('CONTENT_LENGTH', 0))
            data = environ['wsgi.input'].read(length)
            config_file = StringIO.StringIO(data)
            logging.config.fileConfig(config_file)
            start_response("200 OK", [('Content-type', 'text/plain')])
            return "Configutation Loaded"
        else:
            start_response("405 Method not Allowed",
                           [('Content-type', 'text/plain')])
            return "Only POSTing to this resource is supported"


class LogRequestHandler(wsgiref.simple_server.WSGIRequestHandler):

    def log_message(self, *args):
        pass

def start_log_server(port):
    def work():
        server = wsgiref.simple_server.make_server(
            'localhost', port, WSGILoggingApp(),
            handler_class = LogRequestHandler)
        server.serve_forever()
    process = multiprocessing.Process(target = work)
    process.daemon = True
    process.start()
