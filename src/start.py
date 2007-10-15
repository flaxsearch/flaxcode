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
import threading
import traceback

import processing

import cpserver
import flax
from indexserver import indexer
import logclient
import persist
import scheduler
import util

util.setup_psyco()

class StartupOptions(object):
    """Options passed at startup time.

    """
    input_file = None
    output_file = None

    def __init__(self, **kwargs):
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

def parse_cli_opts():
    op = optparse.OptionParser()
    op.add_option('-i', '--input-file',
                  dest = 'input_file',
                  help = "Flax input data file (default is flax.flx)",
                  default = 'flax.flx')
    op.add_option('-o', '--output-file',
                  dest = 'output_file',
                  help = "Flax output data file (default is flax.flx)",
                  default = 'flax.flx')
    (options, args) = op.parse_args()
    return StartupOptions(input_file = options.input_file,
                          output_file = options.output_file)

class FlaxMain():
    """Class controlling starting and stopping Flax.

    Can be used in two ways; synchronously, or asynchronously.

    To use synchronously, the "start" method is called with blocking=True.
    This will block until the server exits, and then clean up all resources.

    To use asynchronously, the "start" method is called with blocking=False.
    This will return immediately.  To cause the server to stop, the stop()
    method is called.  The thread which started the server should later call
    join() to wait for the server to actually stop, and clean up resources
    afterwards.

    """

    def __init__(self, options):
        self.options = options
        self._thread = None
        self._need_cleanup = False

    def _do_start(self):
        """Internal method to actually start all the required processes.

        This blocks until the stop() method is called.

        """
        if self._need_cleanup:
            self._do_cleanup()
        self._need_cleanup = True
        webserver_logconfio = processing.Pipe()
        index_server = indexer.IndexServer()
        logclient.LogConfPub('flaxlog.conf', [webserver_logconfio[0], index_server.logconf_input])
        logclient.LogListener(webserver_logconfio[1]).start()
        logclient.LogConf().update_log_config()
        flax.options = persist.read_flax(self.options.input_file)
        scheduler.ScheduleIndexing(index_server).start()
        persist.DataSaver(self.options.output_file).start()
        cpserver.start_web_server(flax.options, index_server,
                                  'cp.conf')

    def _do_cleanup(self):
        """Internal method to perform all necessary cleanup when shutting down.

        May safely be called when no cleanup is necessary.

        """
        if not self._need_cleanup:
            return
        self._need_cleanup = False
        persist.store_flax(self.options.output_file, flax.options)

    def _do_start_in_thread(self):
        """Method used to start in a separate thread.

        Calls start, and if there's an unhandled exception calls cleanup, and
        handles the exception by printing it to stdout.

        """
        try:
            self._do_start()
        except Exception:
            traceback.print_exc()
            self._do_cleanup()
        except:
            traceback.print_exc()
            self._do_cleanup()
            raise

    def start(self, blocking=True):
        """Start all the Flax threads and processes.

        If blocking is True, this will block until the server is stopped.
        Otherwise, the method will spawn a new thread and return immediately.

        """
        if self._thread is not None:
            self.stop()
            self.join()

        if blocking:
            try:
                self._do_start()
            finally:
                self._do_cleanup()
        else:
            self._thread = threading.Thread(None, self._do_start_in_thread, 'Flax-Main', ())
            self._thread.start()

    def stop(self):
        """Stop any running Flax threads and processes.

        This method returns immediately.  The server may take some time to
        finish.

        Calling it repeatedly is safe, and will have no further effect (unless
        it's been restarted since the previous call).

        """
        cpserver.stop_web_server()

    def join(self):
        """Block until all the Flax threads and processes have finished.

        """
        if self._thread is not None:
            self._thread.join()
            self._thread = None
        self._do_cleanup()


if __name__ == "__main__":
    processing.freezeSupport()
    options = parse_cli_opts()
    main = FlaxMain(options)
    main.start(blocking=True)
