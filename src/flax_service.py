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
"""Start flax as Windows Service.

"""
__docformat__ = "restructuredtext en"


import win32serviceutil
import win32service
import win32event
import win32evtlogutil

import regutil
import win32api
import win32con

#  We need to a lot of messing about with paths, as when running as a service it's not clear what our actual path is. The path to the executable is set in the Registry by the
# installation script.

# Add a suitable path for finding our various modules, otherwise the service won't start properly
import sys
try:
    regpath = win32api.RegQueryValue( regutil.GetRootKey(), "SOFTWARE\\Lemur Consulting Ltd\\Flax\\ModulePath")
except:
    regpath = ""
sys.path.insert(0,regpath)

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

# Fix stdout and stderr and other paths
try:
    mainpath = win32api.RegQueryValue( regutil.GetRootKey(), "SOFTWARE\\Lemur Consulting Ltd\\Flax\\Path")
except:
    mainpath = "c:\\"

# TODO - fix up any other paths

# Prevent buffer overflows by redirecting stdout & stderr to a file
stdoutpath =  "%s\\%s" %(mainpath, './flax_stdout.log')        
stderrpath =  "%s\\%s" %(mainpath, './flax_stderr.log')        


class FlaxService(win32serviceutil.ServiceFramework):

    _svc_name_ = "FlaxService"
    _svc_display_name_ = "Flax Service"
    _svc_deps_ = ["EventLog"]

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        
        # settings file has a fixed name
        options.input_file = 'flax.flx'
	options.output_file = 'flax.flx'


    def SvcStop(self):

        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        # Stop flax
        cherrypy.server.stop()

        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):

        import servicemanager

        # Write a 'started' event to the event log...

        win32evtlogutil.ReportEvent(self._svc_name_,

                                    servicemanager.PYS_SERVICE_STARTED,

                                    0, # category

                                    servicemanager.EVENTLOG_INFORMATION_TYPE,

                                    (self._svc_name_, ''))

        # Redirect stdout and stderr to avoid buffer overflows and to allow debugging while acting as a service      
        sys.stderr = open(stderrpath,'a')
        sys.stdout = open(stdoutpath,'a')

        # Start flax, non-blocking
	#try:
	
	
	
	webserver_logconfio = processing.Pipe()
	index_server = indexer.IndexServer()
	logclient.LogConfPub('flaxlog.conf', [webserver_logconfio[0], index_server.logconf_input])
	logclient.LogListener(webserver_logconfio[1]).start()
	logclient.LogConf().update_log_config()
	flax.options = persist.read_flax(options.input_file)
	scheduler.ScheduleIndexing(index_server).start()
	persist.DataSaver(options.output_file).start()
	cpserver.start_web_server(flax.options, index_server)
		
	
        # wait for being stopped...
        win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)

	# write settings 
	persist.store_flax(options.output_file, flax.options)

        # and write a 'stopped' event to the event log.
        win32evtlogutil.ReportEvent(self._svc_name_,
                                    servicemanager.PYS_SERVICE_STOPPED,
                                    0, # category
                                    servicemanager.EVENTLOG_INFORMATION_TYPE,
                                    (self._svc_name_, ''))


if __name__ == '__main__':
    processing.freezeSupport()
    # Note that this code will not be run in the 'frozen' exe-file!!!

    win32serviceutil.HandleCommandLine(FlaxService)

