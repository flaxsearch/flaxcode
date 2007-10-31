# A distutils setup script for Flax, for use with py2exe
# 
# Creates two executables, startflax.exe for use standalone and
# flaxservice.exe for use as a Windows Service, then
# packages them into setup.exe using InnoSetup.
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
import os
sys.path.insert(0, '..')
sys.path.insert(0, '../src')

################################################################

# This class creates a .iss file for InnoSetup and runs it
class InnoScript:
    def __init__(self,
                 name,
                 this_dir,
                 publisher,
                 homepage,
                 licensefile,
                 version = "NO VERSION"):
        self.this_dir = this_dir
        if not self.this_dir[-1] in "\\/":
            self.this_dir += "\\"
        self.name = name
        self.version = version
        self.publisher = publisher
        self.homepage = homepage
        self.licensefile = licensefile
        self.dist_dir = this_dir + '\dist'
        self.src_dir = this_dir + '\..\src'
        self.output_dir = this_dir + '\package'
        self.localinst_dir = this_dir + '\..\localinst'
        self.windows_dir = '\windows'

    def chop(self, pathname):
        assert pathname.startswith(self.this_dir)
        return pathname[len(self.this_dir):]
    
    def create(self):
        self.pathname = self.this_dir + self.name + ".iss"
        ofi = self.file = open(self.pathname, "w")
        print >> ofi, "; WARNING: This script has been created by py2exe. Changes to this script"
        print >> ofi, "; will be overwritten the next time py2exe is run!"
        print >> ofi, r"[Setup]"
        print >> ofi, r"AppName=%s" % self.name
        print >> ofi, r"AppVerName=%s version %s" % (self.name, self.version)
        print >> ofi, r"DefaultDirName={pf}\%s" % self.name
        print >> ofi, r"DefaultGroupName=%s" % self.name
        print >> ofi, r"AppPublisher=%s" % self.publisher
        print >> ofi, r"AppPublisherURL=%s" % self.homepage
        print >> ofi, r"AppSupportURL=%s" % self.homepage
        print >> ofi, r"AppUpdatesURL=%s" % self.homepage
        print >> ofi, r"LicenseFile=%s" % self.licensefile
        print >> ofi, r"OutputDir=%s" % self.output_dir
        print >> ofi, r"OutputBaseFilename=setup"
        print >> ofi, r"Compression=lzma"
        print >> ofi, r"SolidCompression=yes"
        print >> ofi, r""
        print >> ofi, r'[Languages]'
        print >> ofi, r'Name: "english"; MessagesFile: "compiler:Default.isl"'
        print >> ofi, r""
        print >> ofi, r'[Tasks]'
        print >> ofi, r'Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked'
        print >> ofi, r""
        print >> ofi, r'[Files]'
        print >> ofi, r'Source: "%s\startflax.exe"; DestDir: "{app}"; Flags: ignoreversion' % self.dist_dir
        print >> ofi, r'Source: "%s\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs' % self.dist_dir
        print >> ofi, r'Source: "%s\cp.conf"; DestDir: "{app}\conf"; Flags: ignoreversion' % self.src_dir
        print >> ofi, r'Source: "%s\flaxlog.conf"; DestDir: "{app}\conf"; Flags: ignoreversion' % self.src_dir
        print >> ofi, r'Source: "%s\processing\_processing.pyd"; DestDir: "{app}"; Flags: ignoreversion' % self.localinst_dir
        print >> ofi, r'Source: "%s\htmltotext.pyd"; DestDir: "{app}"; Flags: ignoreversion' % self.localinst_dir
        print >> ofi, r'Source: "%s\msvcr80.dll"; DestDir: "{app}"; Flags: ignoreversion' % self.windows_dir
        print >> ofi, r'Source: "%s\system32\msvcp71.dll"; DestDir: "{app}"; Flags: ignoreversion' % self.windows_dir
        print >> ofi, r'Source: "%s\startflaxservice.bat"; DestDir: "{app}"; Flags: ignoreversion' % self.this_dir
        print >> ofi, r'Source: "%s\stopflaxservice.bat"; DestDir: "{app}"; Flags: ignoreversion' % self.this_dir
        print >> ofi, r'Source: "%s\zlib1.dll"; DestDir: "{app}"; Flags: ignoreversion' % self.this_dir
        print >> ofi, r'Source: "%s\_xapian.pyd"; DestDir: "{app}"; Flags: ignoreversion' % self.this_dir
        print >> ofi, r'; NOTE: Do not use "Flags: ignoreversion" on any shared system files'
        print >> ofi, r""
        print >> ofi, r'[Icons]'
        print >> ofi, r'Name: "{group}\Flax Site Search"; Filename: "{app}\startflax.exe"'
        print >> ofi, r'Name: "{group}\{cm:ProgramOnTheWeb,Flax Site Search}"; Filename: "http://www.flax.co.uk"'
        print >> ofi, r'Name: "{group}\{cm:UninstallProgram,Flax Site Search}"; Filename: "{uninstallexe}"'
        print >> ofi, r'Name: "{commondesktop}\Flax Site Search"; Filename: "{app}\startflax.exe"; Tasks: desktopicon'
        print >> ofi, r""
        print >> ofi, r'[Registry]'
        print >> ofi, r'Root: HKLM; Subkey: "Software\%s"; Flags: uninsdeletekeyifempty' % self.publisher
        print >> ofi, r'Root: HKLM; Subkey: "Software\%s\%s"; Flags: uninsdeletekey' % (self.publisher, self.name)
        print >> ofi, r'Root: HKLM; Subkey: "Software\%s\%s\RuntimePath"; ValueType: string; ValueName: ""; ValueData: "{app}"' % (self.publisher, self.name)
        print >> ofi, r'Root: HKLM; Subkey: "Software\%s\%s\DataPath"; ValueType: string; ValueName: ""; ValueData: "{app}\Data"'  % (self.publisher, self.name)
        print >> ofi, r""
        print >> ofi, r'[Run]'
        print >> ofi, r'; Install & run Service'
        print >> ofi, r'Filename: "{app}\startflaxservice.bat"; Description: "{cm:LaunchProgram,Flax Site Search as a Windows Service}"; Flags: postinstall waituntilterminated '
        print >> ofi, r""
        print >> ofi, r'[UninstallRun]"'
        print >> ofi, r'; Make sure we remove the existing Windows Service'
        print >> ofi, r'Filename: "{app}\stopflaxservice.bat"; Flags: waituntilterminated'


    def compile(self):
        try:
            import ctypes
        except ImportError:
            try:
                import win32api
            except ImportError:
                import os
                os.startfile(self.pathname)
            else:
                print "Using win32api to run InnoSetup."
                win32api.ShellExecute(0, "compile",
                                                self.pathname,
                                                None,
                                                None,
                                                0)
        else:
            print "Using ctypes to run InnoSetup"
            res = ctypes.windll.shell32.ShellExecuteA(0, "compile",
                                                      self.pathname,
                                                      None,
                                                      None,
                                                      0)
            if res < 32:
                raise RuntimeError, "ShellExecute failed, error %d" % res


################################################################
import version
from py2exe.build_exe import py2exe


class build_installer(py2exe):
    # This class creates a Windows installer.
    # You need InnoSetup for it.
    def run(self):
        # First, let py2exe do it's work.
        py2exe.run(self)
        
        # create the Installer, using the files py2exe has created.
        script = InnoScript(name="Flax Site Search",
                            this_dir=os.getcwd(),
                            version=version.get_version_string(),
                            publisher="Lemur Consulting Ltd",
                            homepage="http://www.flax.co.uk",
                            licensefile="gpl.txt")
        print "*** Creating the inno setup script***"
        script.create()
        print "*** Compiling the inno setup script***"
        script.compile()
        # Note: By default the final setup.exe will be in an Output subdirectory.

################################################################
# Py2exe options    
opts = {
    "py2exe": {
        "excludes": "Tkconstants,Tkinter,tcl",
        "dll_excludes": "MSVCP80.dll",
        "packages": "email,dbhash,win32com.ifilter",
#        "compressed": 1,
        "optimize": 2
    }
}

# Define our name & info
class Target:
    def __init__(self, **kw):
        self.__dict__.update(kw)
        # for the versioninfo resources
        self.version = "1.0 beta"
        self.company_name = "Lemur Consulting Ltd"
        self.copyright = "Copyright (c) Lemur Consulting Ltd 2007"
        self.name = "Flax Site Search"
# a NT service, modules is required
flaxservice = Target(
    # used for the versioninfo resource
    description = "Flax Site Search",
    # what to build.  For a service, the module name (not the
    # filename) must be specified!
    modules = ["flaxservice"]
    )
    
################################################################
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
    # use out build_installer class as extended py2exe build command
    cmdclass = {"py2exe": build_installer},
    )
