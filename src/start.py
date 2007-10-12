#!/usr/bin/env python
#
# Copyright (C) 2007 Lemur Consulting Ltd
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
"""Start flax.

"""
__docformat__ = "restructuredtext en"

import setuppaths
import optparse

import processing

import cpserver
import flax
from indexserver import indexer
import logclient
import persist
import scheduler
import util

util.setup_psyco()

def startup():
    op = optparse.OptionParser()
    op.add_option('-i', '--input-file', dest='input_file', help = "Flax input data file (default is flax.flx)", default = 'flax.flx')
    op.add_option('-o', '--output-file', dest='output_file', help= "Flax output data file (default is flax.flx)", default = 'flax.flx')
    (options, args) = op.parse_args()
    try:
        webserver_logconfio = processing.Pipe()
        index_server = indexer.IndexServer()
        logclient.LogConfPub('flaxlog.conf', [webserver_logconfio[0], index_server.logconf_input])
        logclient.LogListener(webserver_logconfio[1]).start()
        logclient.LogConf().update_log_config()
        flax.options = persist.read_flax(options.input_file)
        scheduler.ScheduleIndexing(index_server).start()
        persist.DataSaver(options.output_file).start()
        cpserver.start_web_server(flax.options, index_server)
        print "Flax web server shutting down..."
    finally:
        persist.store_flax(options.output_file, flax.options)

if __name__ == "__main__":
    processing.freezeSupport()
    startup()
