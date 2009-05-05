#!/usr/bin/env python

import sys

import ext

import flax.searchserver
import wsgiwapi
import settings

try:
    settings.settings['data_path'] = sys.argv[1]
except IndexError:
    pass

app = flax.searchserver.App(settings.settings)

server = wsgiwapi.make_server(app, settings.settings['server_bind_address'])
try:
    server.start()
except KeyboardInterrupt:
    server.stop()
