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
"""Start flax as Windows Service.

"""
__docformat__ = "restructuredtext en"

import servicemanager
import win32api
import win32con
import win32service
import win32serviceutil
import win32event
import win32evtlogutil

import os
import sys

from servicemanager import LogInfoMsg, LogErrorMsg

# Get any Registry settings
from flax_w32 import FlaxRegistry
_reg = FlaxRegistry()

# The "processing" module attempts to set a signal handler (by calling
# signal.signal).  However, this is not possible when we're installing as a
# service, since signal.signal only works in the main thread, and we are run in
# a subthread by the service handling code.  Therefore, we install a dummy
# signal handler to avoid an exception being thrown.
# Signals are pretty unused on windows anyway, so hopefully this won't cause a
# problem.  If it does cause a problem, we'll have to work out a way to set a
# signal handler (perhaps, by running the whole of Flax in a sub-process).
def _dummy_signal(*args, **kwargs):
    pass
import signal
signal.signal = _dummy_signal

# Pacify processing 0.35.
# If we don't set argv[0] to '', processing 0.35 will raise an error due to an
# attempt to access sys.modules['__main__'], which doesn't exist when running
# as a service.
if __name__ != '__main__':
    sys.argv[0] = ''

# Before importing the Processing module we have to set sys.executable to point
# at the command-line version of Flax. This means the Processing module will correctly
# run new processes via the freezeSupport() method. However we can't leave it as this
# as Py2exe expects it to be set to the path to the Service executable it builds.
oldsysexec = sys.executable
sys.executable = _reg.runtimepath + '/startflax.exe'

#######################################################
#NOTE: if you need to run the code *non-frozen* ((i.e. 'python flaxservice.py')
# you must replace the above as follows:
# sys.executable = 'c:\Python25\Python.exe'
# (or the equivalent path to a Python interpreter - you may need to read this from the Registry)
# The Services framework will have set it to PythonService.exe, which again won't
# work with the Processing module.
#######################################################

import startflax
import processing
sys.executable = oldsysexec


import flaxpaths

class FlaxService(win32serviceutil.ServiceFramework):

    _svc_name_ = "FlaxService"
    _svc_display_name_ = "Flax Service"
    _svc_deps_ = ["EventLog"]

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        servicemanager.SetEventSourceName(self._svc_display_name_)

        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

        LogInfoMsg('The Flax service is initialising.')

        try:
            # Set options according to our configuration, and create the class
            # which manages starting and stopping the flax threads and processes.
            self._options = startflax.StartupOptions(main_dir = _reg.runtimepath,
                                                    src_dir = _reg.runtimepath,
                                                    dbs_dir = _reg.datapath)
            self._flax_main = startflax.FlaxMain(self._options)
            LogInfoMsg('The Flax service is initialised.')
        except:
            import traceback
            tb=traceback.format_exc()
            LogErrorMsg('Exception during initialisation, traceback follows:\n %s' % tb)            
          

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

        # This call to stop() may take some time, but this shouldn't cause
        # windows to complain because the SvcDoRun thread will have awoken and
        # be sending SERVICE_STOP_PENDING messages every 4 seconds until join()
        # returns True.
        try:
            self._flax_main.stop()
        except:
            import traceback
            tb=traceback.format_exc()
            LogErrorMsg('Exception during SvcStop, traceback follows:\n %s' % tb)            

    def SvcDoRun(self):
        # Write a 'started' event to the event log...
        LogInfoMsg('The Flax service has started.')

        # Redirect stdout and stderr to avoid buffer overflows and to allow
        # debugging while acting as a service
        sys.stderr = open(os.path.join(flaxpaths.paths.log_dir, 'flax_stderr.log'), 'w')
        sys.stdout = open(os.path.join(flaxpaths.paths.log_dir, 'flax_stdout.log'), 'w')

        try:
            # Start flax, non-blocking.
            self._flax_main.start(blocking = False)
            self.ReportServiceStatus(win32service.SERVICE_RUNNING)
            # Wait for message telling us that we're stopping.
            win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)
            LogInfoMsg('The Flax service is stopping.')
            # Wait for the service to stop (and reassure windows that we're still
            # trying to stop).
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING, 5000)
            while not self._flax_main.join(4):
                self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING, 5000)

            # Perform cleanup.
            # This is needed because of a bug in PythonService.exe - it doesn't
            # call Py_Finalize(), so atexit handlers don't get called.  We call
            # processing.process._exit_func() directly as a workaround.  When the
            # bug is fixed, we should stop doing this.  See:
            # https://sourceforge.net/tracker/?func=detail&atid=551954&aid=1273738&group_id=78018
            # for details.
            processing.process._exit_func()

            # Tell windows that we've stopped.
            LogInfoMsg('The Flax service has stopped.')
        except:
            import traceback
            tb=traceback.format_exc()
            LogErrorMsg('Exception during SvcDoRun, traceback follows:\n %s' % tb)            

def ctrlHandler(ctrlType):
    """A windows control message handler.

    This is needed to prevent the service exiting when the user who started it
    exits.

    FIXME - we should probably handle ctrlType = CTRL_SHUTDOWN_EVENT
    differently.

    """
    return True

# Note that this method is never run in the 'frozen' executable, however it may be used for debugging
if __name__ == '__main__':
    processing.freezeSupport()
    win32api.SetConsoleCtrlHandler(ctrlHandler, True)
    win32serviceutil.HandleCommandLine(FlaxService)
