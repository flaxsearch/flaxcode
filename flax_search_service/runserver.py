#!/usr/bin/env python

import ext

import flax.searchserver
import wsgiwapi
import settings

app = flax.searchserver.App(settings.settings)

server = wsgiwapi.make_server(app, settings.settings['server_bind_address'])
try:
    server.start()
except KeyboardInterrupt:
    server.stop()
