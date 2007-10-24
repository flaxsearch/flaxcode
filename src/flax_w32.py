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
"""Start flax as Windows Command Line Application, encapsulate Registry reads.

"""
__docformat__ = "restructuredtext en"


import win32api
import regutil
import os
import sys

REGKEY_BASE = "SOFTWARE\\Lemur Consulting Ltd\\Flax\\"

class FlaxRegistry(object):
    """Encapsulate all the settings we read from the Registry
    """

    # We need to do a lot of messing about with paths, as when running as a frozen executable
    # (under Windows using Py2exe)  it's not clear what our actual path is. 

    def __init__(self):

        self.runtimepath = None
        self.datapath = None
        self.executablepath = None

        try:
            self.runtimepath = win32api.RegQueryValue(regutil.GetRootKey(),
                                            REGKEY_BASE + "RuntimePath")
        except:
            self.runtimepath = r"c:\Program Files\Flax"
    
        try:
            self.datapath = win32api.RegQueryValue(regutil.GetRootKey(),
                                        REGKEY_BASE + "DataPath")
        except:
            self.datapath = r"c:\Program Files\Flax"

        # When running as a Service we need to know where our interpreter is: try and read from the
        # Registry, if this fails try and look somewhere else
        try:
            try:
                exepath = win32api.RegQueryValue(regutil.GetRootKey(),
                                                REGKEY_BASE + "PythonExePath")
            except:
                exepath = win32api.RegQueryValue(regutil.GetRootKey(),
                                                regutil.BuildDefaultPythonKey())
            # If exepath points to a directory, add the name of the default python
            # interpreter to get a path to a file.
            if os.path.isdir(exepath):
                exepath = os.path.join(exepath, 'Python.exe')
            if not os.path.exists(exepath):
                raise ValueError("Python installation not complete (interpreter not "
                                "found at %s)" % exepath)
        except: 
            # No useful registry entries; try looking for Python.exe in the parents of
            # the current value of sys.executable.
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
                raise ValueError("Cannot find python executable (looked in parent "
                                 "directories of %s)" % os.path.dirname(sys.executable))

        self.executablepath = exepath


        
# Import start module, which implements starting and stopping Flax.
import start     
import processing                       
    
if __name__ == "__main__":
    processing.freezeSupport()
    
    _reg = FlaxRegistry()
    # Set options according to our configuration, and create and start the class
    # which manages starting and stopping the flax threads and processes.
    _options = start.StartupOptions(main_dir = _reg.runtimepath,
                                    dbs_dir = _reg.datapath)
    _flax_main = start.FlaxMain(_options)    
    _flax_main.start(blocking = True)
    
    