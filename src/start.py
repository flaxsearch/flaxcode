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
import os
import threading
import traceback

import processing

import cpserver
import flax
import flaxpaths
from indexserver import indexer
import logclient
import persist
import scheduler
import util

util.setup_psyco()

class StartupOptions(object):
    """Options passed at startup time.

    """
    main_dir = None
    dbs_dir = None
    log_dir = None
    conf_dir = None
    var_dir = None

    def __init__(self, **kwargs):
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

def parse_cli_opts():
    op = optparse.OptionParser()
    op.add_option('-d', '--main-dir',
                  dest = 'main_dir',
                  help = 'Flax main directory',
                  default = None)
    op.add_option('--dbs-dir',
                  dest = 'dbs_dir',
                  help = 'Flax database directory (default is <main>/dbs)',
                  default = None)
    op.add_option('--log-dir',
                  dest = 'log_dir',
                  help = 'Flax logfile directory (default is <main>/logs)',
                  default = None)
    op.add_option('--conf-dir',
                  dest = 'conf_dir',
                  help = 'Flax configuration file directory (default is <main>/conf)',
                  default = None)
    op.add_option('--var-dir',
                  dest = 'var_dir',
                  help = 'Flax runtime state directory (default is <main>/var)',
                  default = None)
    (options, args) = op.parse_args()
    if options.main_dir is None:
        options.main_dir = os.path.join(os.path.dirname(__file__), 'data')
    return StartupOptions(main_dir = options.main_dir,
                          dbs_dir = options.dbs_dir,
                          log_dir = options.log_dir,
                          conf_dir = options.conf_dir,
                          var_dir = options.var_dir)

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
        paths = flaxpaths.paths
        paths.set_dirs(options.main_dir, options.dbs_dir, options.log_dir,
                       options.conf_dir, options.var_dir)
        paths.makedirs()

        self._thread = None
        self._need_cleanup = False

    def _do_start(self):
        """Internal method to actually start all the required processes.

        This blocks until the stop() method is called.

        """
        if self._need_cleanup:
            self._do_cleanup()
        self._need_cleanup = True

        flax.options = persist.read_flax(flaxpaths.flaxstate_path)

        webserver_logconfio = processing.Pipe()
        index_server = indexer.IndexServer()
        logclient.LogConfPub(flaxpaths.paths.logconf_path,
                             [webserver_logconfio[0], index_server.logconf_input])
        logclient.LogListener(webserver_logconfio[1]).start()
        logclient.LogConf(flaxpaths.paths.logconf_path).update_log_config()
        scheduler.ScheduleIndexing(index_server).start()
        persist.DataSaver(flaxpaths.flaxstate_path).start()
        cpserver.start_web_server(flax.options, index_server,
                                  flaxpaths.paths.cpconf_path)

    def _do_cleanup(self):
        """Internal method to perform all necessary cleanup when shutting down.

        May safely be called when no cleanup is necessary.

        """
        if not self._need_cleanup:
            return
        self._need_cleanup = False
        persist.store_flax(flaxpaths.flaxstate_path, flax.options)

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
