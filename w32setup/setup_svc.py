# A distutils setup script for Flax, for use with py2exe
# 
# Creates two executables, startflax.exe for use standalone and
# flaxservice.exe for use as a Windows Service
#
import sys

# This next section taken from http://www.py2exe.org/index.cgi/WinShell
# ModuleFinder can't handle runtime changes to __path__, but win32com uses them
try:
     # if this doesn't work, try import modulefinder
    import py2exe.mf as modulefinder
    import win32com
    for p in win32com.__path__[1:]:
         modulefinder.AddPackagePath("win32com", p)
    for extra in ["win32com.shell"]: #,"win32com.mapi"
        __import__(extra)
        m = sys.modules[extra]
        for p in m.__path__[1:]:
            modulefinder.AddPackagePath(extra, p)
except ImportError:
    # no build path setup, no worries.
    pass


from distutils.core import setup
import py2exe

import glob

sys.path.insert(0, '..')
sys.path.insert(0, '../src')


class Target:
    def __init__(self, **kw):
        self.__dict__.update(kw)
        # for the versioninfo resources
        self.version = "1.0 beta"
        self.company_name = "Lemur Consulting Ltd"
        self.copyright = "Copyright (c) Lemur Consulting Ltd 2007"
        self.name = "Flax Site Search"

################################################################
# a NT service, modules is required
flaxservice = Target(
    # used for the versioninfo resource
    description = "Flax Site Search",
    # what to build.  For a service, the module name (not the
    # filename) must be specified!
    modules = ["flaxservice"]
    )

# Py2exe options    
opts = {
    "py2exe": {
        "excludes": "Tkconstants,Tkinter,tcl",
        "dll_excludes": "MSVCP80.dll",
        "packages": "email,dbhash,win32com.ifilter",
    }
}

setup(
    # We take our dependencies from the localinst folder. The rest is picked up from the main Python folder
    options=opts,
    package_dir = {'': '../localinst'},
    packages = ['cherrypy', 'cherrypy.lib', 'cherrypy.wsgiserver', 'processing', 'xappy'
                ],
    py_modules = ['HTMLTemplate'],
    
    # Other files we need
    data_files=[
                ("templates",
                glob.glob('../src/templates/*.html')),
                ("templates",
                glob.glob('../src/templates/*.js')),

                ("static/css",
                glob.glob('../src/static/css/*.css')),
                ("static/img",
                glob.glob('../src/static/img/*.gif')),
                ("static/img",
                glob.glob('../src/static/img/*.png')),
                ("static/img",
                glob.glob('../src/static/img/*.ico')),
                ("static/js",
                glob.glob('../src/static/js/*.js')),
                
                ],

    # targets to build
    console = ["../src/startflax.py"],
    service = [flaxservice],
    
    )
