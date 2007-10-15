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

import regutil
import servicemanager
import win32api
import win32con
import win32service
import win32serviceutil
import win32event
import win32evtlogutil

import os
import sys
import threading

# We need to do a lot of messing about with paths, as when running as a service
# it's not clear what our actual path is. The path to the executable is set in
# the Registry by the installation script.

REGKEY_BASE = "SOFTWARE\\Lemur Consulting Ltd\\Flax\\"

# Add a suitable path for finding our various modules, otherwise the service
# won't start properly.
try:
    modulepath = win32api.RegQueryValue(regutil.GetRootKey(),
                                     REGKEY_BASE + "\\ModulePath")
except:
    modulepath = "c:\Program Files\Flax"
sys.path.insert(0,modulepath)

# Work out the top path for all logs and settings used by Flax.
try:
    mainpath = win32api.RegQueryValue(regutil.GetRootKey(),
                                      REGKEY_BASE + "\\Path")
except:
    mainpath = "c:\Program Files\Flax"
    


# We have to set sys.executable to a normal Python interpreter.  It won't point
# to one because we will have been run by PythonService.exe (and sys.executable
# will be the path to that executable).  However, the "processing" extension
# module uses sys.executable to emulate a fork, and needs it to be the correct
# python interpreter.  We'll try to read it from a registry entry, and try
# making it up otherwise.
try:
    exedir = win32api.RegQueryValue(regutil.GetRootKey(),
                                     regutil.BuildDefaultPythonKey())
    exepath = os.path.join(exedir, 'Python.exe')
    if not os.path.exists(exepath):
        raise ValueError("Python installation not complete")
except:
    exedir = sys.executable
    while True:
        newdir = os.path.dirname(exedir)
        if newdir == exedir:
            break
        exedir = newdir
        exepath = os.path.join(exedir, 'Python.exe')
        if os.path.exists(exepath):
            break
    if not os.path.exists(exepath):
        raise ValueError("Cannot determine python executable")
sys.executable = exepath

# TODO - fix up any other paths

# Prevent buffer overflows by redirecting stdout & stderr to a file
stdoutpath = os.path.join(mainpath, 'flax_stdout.log')
stderrpath = os.path.join(mainpath, 'flax_stderr.log')

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


# Import start module, which implements starting and stopping Flax.
import start


class FlaxService(win32serviceutil.ServiceFramework):

    _svc_name_ = "FlaxService"
    _svc_display_name_ = "Flax Service"
    _svc_deps_ = ["EventLog"]

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

        settings_path = os.path.join(mainpath, 'flax.flx')
        self._options = start.StartupOptions(input_file = settings_path,
                                             output_file = settings_path)
        self._flax_main = start.FlaxMain(self._options, modulepath)


    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        # Write a 'started' event to the event log...
        win32evtlogutil.ReportEvent(self._svc_name_,
                                    servicemanager.PYS_SERVICE_STARTED,
                                    0, # category
                                    servicemanager.EVENTLOG_INFORMATION_TYPE,
                                    (self._svc_name_, ''))

        # Redirect stdout and stderr to avoid buffer overflows and to allow
        # debugging while acting as a service
        sys.stderr = open(stderrpath, 'a')
        sys.stdout = open(stdoutpath, 'a')

        try:
            try:
                try:
                    # Start flax, non-blocking
                    self._flax_main.start(blocking = False)

                    # Wait for message telling us to stop.
                    win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)
                except:
                    import traceback
                    traceback.print_exc()
            finally:
                try:
                    # Tell Flax to stop, and wait for it to stop.
                    self._flax_main.stop()
                    self._flax_main.join()
                except:
                    import traceback
                    traceback.print_exc()
        finally:
            # and write a 'stopped' event to the event log.
            win32evtlogutil.ReportEvent(self._svc_name_,
                                        servicemanager.PYS_SERVICE_STOPPED,
                                        0, # category
                                        servicemanager.EVENTLOG_INFORMATION_TYPE,
                                        (self._svc_name_, ''))

def ctrlHandler(ctrlType):
    """A windows control message handler.

    This is needed to prevent the service exiting when the user who started it
    exits.

    FIXME - we should probably handle ctrlType = CTRL_SHUTDOWN_EVENT
    differently.

    """
    return True

if __name__ == '__main__':
    import processing
    processing.freezeSupport()

    win32api.SetConsoleCtrlHandler(ctrlHandler, True)
    win32serviceutil.HandleCommandLine(FlaxService)
