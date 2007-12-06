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
import getpass
import optparse
import os
import sys
import threading
import time
import logging

import processing
import cpserver
import flax
import flaxauth
import flaxpaths
from indexserver import indexer
import logclient
import persist
import scheduler
import version
import util

util.setup_psyco()


log = logging.getLogger()

class StartupOptions(object):
    """Options passed at startup time.

    """
    main_dir = None
    src_dir = None
    dbs_dir = None
    log_dir = None
    conf_dir = None
    var_dir = None

    def __init__(self, **kwargs):
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

def parse_cli_opts():
    op = optparse.OptionParser(version="Flax version: " + version.get_version_string())
    windows = (sys.platform == "win32")
    # On Windows, we use the paths set in the Registry unless overridden by a command line option
    if windows:
        import flax_w32
        reg = flax_w32.FlaxRegistry()

    op.add_option('-d', '--main-dir',
                  dest = 'main_dir',
                  help = 'Flax main directory',
                  default = reg.runtimepath if windows else os.path.join(os.path.dirname(__file__), 'data'))
    op.add_option('--src-dir',
                  dest = 'src_dir',
                  help = 'Flax code directory',
                  default = reg.runtimepath if windows else os.path.dirname(__file__))
    op.add_option('--dbs-dir',
                  dest = 'dbs_dir',
                  help = 'Flax database directory (default is <main>/dbs)',
                  default = reg.datapath if windows else None)
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

    op.add_option('--set-admin-password',
                  dest = 'set_admin_password',
                  help = 'Set the administrator password (and then exit)',
                  action = 'store_true',
                  default = False)

    (options, args) = op.parse_args()
    realpath = lambda x: os.path.realpath(x) if x else None
    return StartupOptions(main_dir = realpath(options.main_dir),
                          src_dir = realpath(options.src_dir),
                          dbs_dir = realpath(options.dbs_dir),
                          log_dir = realpath(options.log_dir),
                          conf_dir = realpath(options.conf_dir),
                          var_dir = realpath(options.var_dir),
                          set_admin_password = options.set_admin_password)

class FlaxMain(object):
    """Class controlling starting and stopping Flax.

    Can be used in two ways; synchronously, or asynchronously.

    To use synchronously, the "start" method is called with blocking=True.
    This will block until the server exits, and then clean up all resources.

    To use asynchronously, the "start" method is called with blocking=False.
    This will return immediately.  To cause the server to stop, the stop()
    method is called.

    """
    def __init__(self, options):
        flaxpaths.paths.set_dirs(options.main_dir, options.src_dir,
                                 options.dbs_dir, options.log_dir,
                                 options.conf_dir, options.var_dir)
        flaxpaths.paths.makedirs()
        self._stop_thread = None
        self._need_cleanup = False

    def _do_start(self, blocking):
        """Internal method to actually start all the required processes.

        This blocks until the stop() method is called.

        """
        if self._need_cleanup:
            self._do_cleanup()
        self._need_cleanup = True
        flaxauth.load()
        webserver_logconfio = processing.Pipe()
        self.index_server = indexer.IndexServer()
        logclient.LogConfPub(flaxpaths.paths.logconf_path,
                             [webserver_logconfio[0], self.index_server.log_config_listener()])
        logclient.LogListener(webserver_logconfio[1]).start()
        logclient.LogConf(flaxpaths.paths.logconf_path).update_log_config()
        persist.read_flax(flaxpaths.paths.flaxstate_path, flax.options)
        scheduler.ScheduleIndexing(self.index_server).start()
        persist.DataSaver(flaxpaths.paths.flaxstate_path).start()
        cpserver.start_web_server(flax.options, self.index_server,
                                  flaxpaths.paths.cpconf_path,
                                  flaxpaths.paths.templates_path,
                                  blocking)

    def _do_stop(self):
        """Internal method to perform all necessary cleanup when shutting down.

        May safely be called when no cleanup is necessary.

        """
        if not self._need_cleanup:
            log.debug("_do_stop: no cleanup needed, returning")
            return
        self._need_cleanup = False
        if self.index_server:
            log.debug("_do_stop: Telling index_server to stop")
            self.index_server.stop()
        log.debug("_do_stop: storing persistent data")
        persist.store_flax(flaxpaths.paths.flaxstate_path, flax.options)
        log.debug("_do_stop: stopping web server")
        cpserver.stop_web_server()
        if self.index_server:
            log.debug("_do_stop: joining index_server")
            self.index_server.join()
            log.debug("FlaxMain._do_stop: joined index_server")

    def start(self, blocking=True):
        """Start all the Flax threads and processes.

        If blocking is True, this will block until the server is
        stopped.  Otherwise, the method will return immediately, in
        which case stop should be called to terminate.

        """
        self._do_start(blocking)

    def stop(self):
        """Stop any running Flax threads and processes.

        This method returns immediately.  The server may take some time to
        finish.

        Calling it repeatedly is safe, and will have no further effect (unless
        it's been restarted since the previous call).

        """
        log.debug("Creating stopping thread")
        self._stop_thread = threading.Thread(target=self._do_stop)
        self._stop_thread.start()
        log.debug("Stopping thread started")

    def join(self, timeout=None):
        """Block until all the Flax threads and processes have
        finished.


        If timeout is specified, it is the maximum time (in seconds) which the
        call will block for.

        Return True if all threads and processes have finished.  Otherwise,
        returns False.

        """
        if self._stop_thread:
#            log.debug("FlaxMain.join: joining _stop_thread timeout is %d" % timeout)
            self._stop_thread.join(timeout)
            return not self._stop_thread.isAlive()
        else:
            # there's no stop thread, so stop() has not been called yet.
            # sleep here for a bit so something else can call stop if need be.
            log.debug("FlaxMain.join: no stop thread, not sure we should be here")
            time.sleep(1)
            return False

def set_admin_password():
    """Get a new administrator password (from stdin) and store it.
    
    The password is stored in the appropriate configuration file.

    """
    print """
Enter a new administrator password.  This is needed to allow access to the
administrator section of the Flax interface.

The password is case sensitive.  You will be asked to enter it twice, to guard
against typing errors.

""".strip() + '\n'
    while True:
        pw1 = getpass.getpass('New password:')
        pw2 = getpass.getpass('New password again, to check:')
        if pw1 != pw2:
            print "Passwords differ - try again"
            print
            continue
        if pw1 == '':
            print "No password entered - try again"
            print
            continue
        break
    if os.path.exists(flaxpaths.paths.authconf_path):
        flaxauth.load()
    flaxauth.set('admin', pw1)
    flaxauth.save()

def main():
    processing.freezeSupport()
    options = parse_cli_opts()
    main = FlaxMain(options)
    if options.set_admin_password:
        set_admin_password()
        sys.exit(0)
    try:
        main.start(blocking=True)
    except:
        main.stop()
        main.join()
        raise

if __name__ == "__main__":
   main()
    
