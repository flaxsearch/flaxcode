#!/usr/bin/env python

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ext'))

import flax.searchserver
import wsgiwapi

app = flax.searchserver.App()

server = wsgiwapi.make_server(app, ('0.0.0.0', 8080))
try:
    server.start()
except KeyboardInterrupt:
    server.stop()
