# Copyright (C) 2009, 2010 Lemur Consulting Ltd
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

# Some code partially based on
# http://nick.vargish.org/clues/python-tricks.html - not sure who owns
# the copyright

import logging
import logging.config
import os
import sys
import signal
import subprocess
import multiprocessing
import copy

def is_windows():
    """
    Determine if we are running under some windows flavour
    """
    return (sys.platform == "win32")
    

# OO paths etc.
ooo_base_path = 'c:/Program Files/OpenOffice.org 3/'
ooo_python_paths = ['c:/Program Files/OpenOffice.org 3/Basis/program']
ooo_environment_PATH =  (';' + ooo_base_path + 'URE/bin;' +
                          ooo_base_path + 'Basis/Program')
ooo_environment_URE_BOOTSTRAP = ooo_base_path + 'program/fundamental.ini'
ooo_connection_string = (
    "uno:socket,host=localhost,port=8100;urp;StarOffice.ComponentContext")

def fixup_ooo_environ():
    """
    On windows using uno is tricky since it really expects to be
    run using the version of python shipped with Ooo. Calling this
    should fix things, but note that you still need to be binary
    compatible (probably exactly the same version of python). If you
    want to use a different version of python you will need to rebuild
    the pyuno module.
    """
    if is_windows():
        sys.path = sys.path + ooo_python_paths
        os.environ['PATH'] = os.environ['PATH'] + ooo_environment_PATH
        url = copy.copy(ooo_environment_URE_BOOTSTRAP)
        url = url.replace(' ', '%20')
        url = 'file:///'+url
        os.environ['URE_BOOTSTRAP'] = url

def initialise_logging():
    """
    Initialise the Python logger with our config
    """
    logging.config.fileConfig("logging.conf")

class TimeOutException(Exception):
    pass

class TimedFunction(object):

    def __init__(self, fn, timeout):
        self.fn = fn
        self.timeout = timeout

    def handle_timeout(self, signum, frame):
        raise TimeOutException()

    def __call__(self, *args):
        old = signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.timeout)
        try:
            result = self.fn(*args)
        finally:
            signal.signal(signal.SIGALRM, old)
        signal.alarm(0)
        return result

def kill_oo_by_port(port=0, logger=None):
    """
    Find and kill an instance of Open Office
    """
    if is_windows():
        import win32api, win32con
        # FIXME we must find the instance of OO running on this port! Only necessary if we're
        # running multiple copies of OO that might die, of course.
    #        handle = win32api.OpenProcess( win32con.PROCESS_TERMINATE, 0, pid )
    #       win32api.TerminateProcess( handle, 0 )
    #        win32api.CloseHandle( handle )
    else:
        ps_list = ["/bin/ps", "-ww", "-eopid,args"]
        grep_list = ["/bin/grep", 'soffice.bin.*port={port}.*'.format(port=port)]
        skip_list = ["/bin/grep", "-v", "grep"]
        p1 = subprocess.Popen(ps_list, stdout=subprocess.PIPE)
        p2 = subprocess.Popen(grep_list, stdin=p1.stdout, stdout=subprocess.PIPE)
        p3 = subprocess.Popen(skip_list, stdin=p2.stdout, stdout=subprocess.PIPE)
        
        output = p3.communicate()[0]
        pid = int(output.strip().split(" ")[0])
        os.kill(pid, signal.SIGKILL)
        if logger:
            logger.warn("killed oo process with pid: " + str(pid))
    

class FilterRunner(multiprocessing.Process):
    """
    A class for running a filter as a process, used by RemoteFilterRunner
    """
    def __init__(self, filter_maker, filter_arg, i, o):
        super(FilterRunner, self).__init__()
        self.i = i
        self.o = o
        self.filter_maker = filter_maker
        self.filter_arg = filter_arg
        self.daemon = True
        self.start()
        # Since we will run under multiprocessing we need to use a different logger
        #self.logger = multiprocessing.log_to_stderr()
        #self.logger = multiprocessing.get_logger()
        #self.logprefix = "remote_filter.remote" + " : "
        #self.logger.setLevel(logging.DEBUG)
        
    def run(self):
        """Repeatedly receive a filename on `self.i`, run
        self.filter on that file, send output to `o`"""
        self.filter = self.filter_maker(self.filter_arg)
        
        while 1:
            filename = self.i.recv()
            mimetype = self.i.recv()
            try:
                results = self.filter(filename, mimetype)
                # because the filter returns an iterator we won't
                # see all errors until we actually compute the
                # values so this next needs to be in the try
                # block as well.
                if not isinstance(results, Exception):
                    results = list(results)
            except Exception, e:
                self.logger.error("FilterRunner: %s caught exception: %s\n filename: %s" % (str(self), str(e), filename))
            self.o.send(results)

class TimeOutError(Exception):
    """
    Signal that a remote filter is taking too long to process a file
    """
    pass

class RemoteFilterRunner(object):
    """
    A filter that runs another filter in a subprocess, with a timeout.
    """

    def __init__(self, filter_maker, port, 
                 cleanup, timeout=10, restart_limit=1000):
        self.logger = logging.getLogger("remote_filter")
        self.filter_maker = filter_maker
        self.cleanup = cleanup
        self.port = port
        self.timeout = timeout
        self.server = None
        self.restart_limit = restart_limit
        # count is the number of calls we've processed since the remote process was started.
        self.count = 0
        self.pid = 0

    def __call__(self, file_name, mimetype):
        self.count += 1
        if self.count > self.restart_limit:
            self.kill_server()
        self.maybe_start_server()
        self.outpipe[0].send(file_name)
        self.outpipe[0].send(mimetype)
        if self.inpipe[1].poll(self.timeout):
            blocks = self.inpipe[1].recv()
            if isinstance(blocks, Exception):
                # if there was an exception raised then we should
                # restart the remote process immediately
                # otherwise the next document may timeout because the
                # remote process is not responding
                self.logger.warning(
                    "Killing remote filter - it raised the exception: %s" % str(blocks))
                self.kill_server()
            else:
                for block in blocks:
                    yield block
        else:
            self.logger.warning("Killing remote filter due to timeout")
            self.kill_server()
            self.logger.warning(
                "The server took too long to process file %s, giving up" % file_name)

    def kill_server(self):
        
        if self.server:
            self.logger.info(
                "killing remote filter process with pid: %d" % self.server.pid)
            self.server.terminate()
            if self.cleanup:
                self.cleanup(port=self.port, logger=self.logger)
        else:
            self.logger.warning("kill server called when no server")
        self.count = 0
        self.server = self.inpipe = self.outpipe = None

    def maybe_start_server(self):
        if ((not self.server) or (self.server and not self.server.is_alive())):
            if self.server:
                self.kill_server()
            self.inpipe = multiprocessing.Pipe()
            self.outpipe = multiprocessing.Pipe()
            self.server = FilterRunner(
                self.filter_maker,
                self.port,
                self.outpipe[1], 
                self.inpipe[0])
            self.logger.info(
                "Starting a remote filter process with pid: %d (%s:%s)" % (self.server.pid, self.filter_maker, self.port))
