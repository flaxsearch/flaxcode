#!/usr/bin/env python

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ext'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ext', 'wsgiwapi'))

import flax.searchserver
import wsgiwapi
import settings

app = flax.searchserver.App(settings.settings)

server = wsgiwapi.make_server(app, ('0.0.0.0', 8080))
try:
    server.start()
except KeyboardInterrupt:
    server.stop()
