# A distutils setup script for Flax, for use with py2exe

# Copyright (C) Lemur Consulting Ltd 2007
# This file is a modified version of the example from the py2exe distribution.

# When run as "python setup_svc.py py2exe", creates two executables,
# startflax.exe for use standalone and flaxservice.exe for use as a Windows
# Service, then packages them into setup.exe using InnoSetup.

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
                 versionA,
                 versionB,
                 versionC,
                 versionD):
        self.this_dir = this_dir
        if not self.this_dir[-1] in "\\/":
            self.this_dir += "\\"
        self.name = name
        self.versionA = versionA
        self.versionB = versionB
        self.versionC = versionC
        self.versionD = versionD
        self.publisher = publisher
        self.homepage = homepage
        self.licensefile = licensefile
        self.dist_dir = this_dir + '\dist'
        self.src_dir = this_dir + '\..\src'
        self.output_dir = this_dir + '\package'
        self.localinst_dir = this_dir + '\..\localinst'

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
        print >> ofi, r"AppVerName=%s version %s.%s.%s.%s" % (self.name, self.versionA, self.versionB, self.versionC, self.versionD)
        print >> ofi, r"VersionInfoVersion=%s.%s.%s.%s" % (self.versionA, self.versionB, self.versionC, self.versionD)
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
        print >> ofi, r"SetupIconFile=install.ico"
        print >> ofi, r"WizardImageFile=install.bmp"
        print >> ofi, r"WizardSmallImageFile=install_small.bmp"
        print >> ofi, r"WizardImageStretch=no"
        print >> ofi, r"WizardImageBackColor=$FFFFFF"
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
        print >> ofi, r'Source: "%s\cp.conf"; DestDir: "{app}\conf"; Flags: onlyifdoesntexist ' % self.src_dir
        print >> ofi, r'Source: "%s\flaxlog.conf"; DestDir: "{app}\conf"; Flags: onlyifdoesntexist ' % self.src_dir
        print >> ofi, r'Source: "%s\processing\_processing.pyd"; DestDir: "{app}\localinst"; Flags: ignoreversion' % self.localinst_dir
        print >> ofi, r'Source: "%s\htmltotext.pyd"; DestDir: "{app}\localinst"; Flags: ignoreversion' % self.localinst_dir
        print >> ofi, r'Source: "%s\msvcp80.dll"; DestDir: "{sys}"; Flags: onlyifdoesntexist sharedfile restartreplace uninsneveruninstall' % self.this_dir
        print >> ofi, r'Source: "%s\msvcr80.dll"; DestDir: "{sys}"; Flags: onlyifdoesntexist sharedfile restartreplace uninsneveruninstall' % self.this_dir
        print >> ofi, r'Source: "%s\msvcp71.dll"; DestDir: "{sys}"; Flags: onlyifdoesntexist sharedfile restartreplace uninsneveruninstall' % self.this_dir
        print >> ofi, r'Source: "%s\startflaxservice.bat"; DestDir: "{app}"; Flags: ignoreversion' % self.this_dir
        print >> ofi, r'Source: "%s\stopflaxservice.bat"; DestDir: "{app}"; Flags: ignoreversion' % self.this_dir
        print >> ofi, r'Source: "%s\zlib1.dll"; DestDir: "{app}\localinst"; Flags: ignoreversion' % self.this_dir
        print >> ofi, r'Source: "%s\exampledocs\*"; DestDir: "{app}\exampledocs"; Flags: ignoreversion' % self.this_dir
        print >> ofi, r'Source: "%s\gettingstarted\*"; DestDir: "{app}\gettingstarted"; Flags: ignoreversion' % self.this_dir
        print >> ofi, r'Source: "%s\*.ico"; DestDir: "{app}"; Flags: ignoreversion' % self.this_dir
        print >> ofi, r'; NOTE: Do not use "Flags: ignoreversion" on any shared system files'
        print >> ofi, r""
        print >> ofi, r'[Icons]'
        print >> ofi, r'Name: "{group}\%s (Manual Start)"; Filename: "{app}\startflax.exe"; IconFilename: "{app}\install.ico"' % self.name
        print >> ofi, r'Name: "{group}\{cm:ProgramOnTheWeb,%s}"; Filename: "http://www.flax.co.uk"' % self.name
        print >> ofi, r'Name: "{group}\Getting Started Guide"; Filename: "file://{app}\gettingstarted\GettingStartedOnWindows.htm"' 
        print >> ofi, r'Name: "{group}\{cm:UninstallProgram,%s}"; Filename: "{uninstallexe}"; IconFilename: "{app}\uninstall.ico"' % self.name
        print >> ofi, r'Name: "{commondesktop}\%s"; Filename: "{app}\startflax.exe"; Tasks: desktopicon; IconFilename: "{app}\install.ico"' % self.name
        print >> ofi, r""
        print >> ofi, r'[Registry]'
        print >> ofi, r'Root: HKLM; Subkey: "Software\%s"; Flags: uninsdeletekeyifempty' % self.publisher
        print >> ofi, r'Root: HKLM; Subkey: "Software\%s\%s"; Flags: uninsdeletekey' % (self.publisher, self.name)
        print >> ofi, r'Root: HKLM; Subkey: "Software\%s\%s\RuntimePath"; ValueType: string; ValueName: ""; ValueData: "{app}"' % (self.publisher, self.name)
        print >> ofi, r'Root: HKLM; Subkey: "Software\%s\%s\DataPath"; ValueType: string; ValueName: ""; ValueData: "{code:GetDataDir}"'  % (self.publisher, self.name)
        print >> ofi, r""
        print >> ofi, r'[Run]'
        print >> ofi, r'; Set admin password'
        print >> ofi, r'Filename: "{app}\startflax.exe"; StatusMsg: "Setting administration password"; Parameters: "--set-admin-password"; Flags: waituntilterminated'
        print >> ofi, r'; Install & run Service'
        print >> ofi, r'Filename: "{app}\startflaxservice.bat"; Description: "{cm:LaunchProgram,%s as a Windows Service}"; Flags: postinstall waituntilterminated ' % self.name
        print >> ofi, r'Filename: "{app}\gettingstarted\GettingStartedOnWindows.htm"; Description: "Read the Getting Started guide"; Flags: postinstall shellexec'
        print >> ofi, r""
        print >> ofi, r'[Dirs]'
        print >> ofi, r'Name: {code:GetDataDir}; Flags: uninsneveruninstall'
        print >> ofi, r""
        print >> ofi, r'[Code]'
        print >> ofi, r'var'
        print >> ofi, r'DataDirPage: TInputDirWizardPage;'
        print >> ofi, r'LightMsgPage: TOutputMsgWizardPage;'
        print >> ofi, r""
        print >> ofi, r'function InitializeSetup(): Boolean;'
        print >> ofi, r'begin'
        print >> ofi, r"{ Check if our registry key exists, in which case assume we're already installed }"
        print >> ofi, r"if RegKeyExists(HKLM, 'Software\%s\%s') then begin"  % (self.publisher, self.name)
        print >> ofi, r"    MsgBox('%s:'#13#13'Flax is already installed. Please uninstall the previous version before installing this version.'#13#13'There is an option to uninstall in Start, Programs, %s', mbError, MB_OK);" % (self.name, self.name)
        print >> ofi, r'    Result := False;'
        print >> ofi, r'  end else'
        print >> ofi, r'    Result := True;'
        print >> ofi, r'end;        '
        print >> ofi, r""
        print >> ofi, r'procedure InitializeWizard;'
        print >> ofi, r'begin'
        print >> ofi, r'{ Create the pages } '
        print >> ofi, r''
        print >> ofi, r"DataDirPage := CreateInputDirPage(wpSelectDir,"
        print >> ofi, r"    'Select Data Directory', 'Where should data files be stored?',"
        print >> ofi, r"    'Select the folder in which %s should store its data files, then click Next. '#13#13 +" % self.name
        print >> ofi, r"    'Note that Flax data files can be very large, so you may want to store them on a separate ' +"
        print >> ofi, r"    'disk or partition.',"
        print >> ofi, r"    False, '');"
        print >> ofi, r"DataDirPage.Add('');"
        print >> ofi, r""
        print >> ofi, r"LightMsgPage := CreateOutputMsgPage(wpPreparing,"
        print >> ofi, r"    'Set Administration Password', 'Set Administration Password',"
        print >> ofi, r"    'After installation, Setup will ask you to enter a password for the Administration pages of %s.'#13#13 +" % self.name
        print >> ofi, r"    'To view these pages you will need to use a username of " + '"admin"' + " and the password you choose. '#13#13 +"
        print >> ofi, r"    'You will be asked to confirm the password by typing it twice.');"
        print >> ofi, r""
        print >> ofi, r"end;"
        print >> ofi, r""
        print >> ofi, r"function NextButtonClick(CurPageID: Integer): Boolean;"
        print >> ofi, r"var"
        print >> ofi, r"I: Integer;"
        print >> ofi, r"begin"
        print >> ofi, r"{ Validate certain pages before allowing the user to proceed }"
        print >> ofi, r"if CurPageID = wpSelectDir then begin"
        print >> ofi, r"    { Set initial value }"
        print >> ofi, r"    DataDirPage.Values[0] := ExpandConstant('{app}\Data')" 
        print >> ofi, r"    end;"
        print >> ofi, r"if CurPageID = DataDirPage.ID then begin"
        print >> ofi, r"if DataDirPage.Values[0] = '' then"
        print >> ofi, r"    DataDirPage.Values[0] := ExpandConstant('{app}\Data')" 
        print >> ofi, r"    Result := True;"
        print >> ofi, r"    end;"
        print >> ofi, r"Result := True;"
        print >> ofi, r"end;"
        print >> ofi, r""
        print >> ofi, r"function GetDataDir(Param: String): String;"
        print >> ofi, r"begin"
        print >> ofi, r'{ Return the selected DataDir }'
        print >> ofi, r"Result := DataDirPage.Values[0];"
        print >> ofi, r"end;"        
        print >> ofi, r""
        print >> ofi, r"function InitializeUninstall(): Boolean;  "
        print >> ofi, r"{ Ask the user if they want to uninstall everything }"
        print >> ofi, r"var"
        print >> ofi, r"SetDataPath: String;"
        print >> ofi, r"ResultCode: Integer;"
        print >> ofi, r"AlreadyStoppedSvc: Boolean;"
        print >> ofi, r"begin"
        print >> ofi, r"  AlreadyStoppedSvc := False;"
        print >> ofi, r"  if MsgBox('Do you want to remove ALL %s data - be careful, this includes settings and all indexes! Click No if you are upgrading to a newer version of %s',mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES then begin" % (self.name,self.name)
        print >> ofi, r"    { First stop the service, so we can delete files }"
        print >> ofi, r"    Exec(ExpandConstant('{app}\stopflaxservice.bat'), '', '', SW_SHOW,ewWaitUntilTerminated, ResultCode);"
        print >> ofi, r"    AlreadyStoppedSvc := True;"
        print >> ofi, r"    DelTree(ExpandConstant('{app}')+'\conf',True,True,True);"
        print >> ofi, r"    DelTree(ExpandConstant('{app}')+'\var',True,True,True);"
        print >> ofi, r"    DelTree(ExpandConstant('{app}')+'\logs',True,True,True);"
        print >> ofi, r"    if RegKeyExists(HKLM, 'Software\%s\%s') then "  % (self.publisher, self.name)
        print >> ofi, r"       if RegQueryStringValue(HKEY_LOCAL_MACHINE, 'Software\%s\%s\DataPath','', SetDataPath) then " % (self.publisher, self.name)
        print >> ofi, r"         DelTree(SetDataPath,True,True,True);"
        print >> ofi, r"  end;"
        print >> ofi, r"  if AlreadyStoppedSvc then"
        print >> ofi, r"    Result:=True"
        print >> ofi, r"  else begin"
        print >> ofi, r"    { We have to ask if they're going on to remove the program as if so, and we haven't stopped the svc, we should }"
        print >> ofi, r"    if MsgBox('Do you want to remove the %s program? Click Yes if you are upgrading to a newer version of %s',mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES then begin" % (self.name,self.name)
        print >> ofi, r"      Exec(ExpandConstant('{app}\stopflaxservice.bat'), '', '', SW_SHOW,ewWaitUntilTerminated, ResultCode);"
        print >> ofi, r"      Result := True;"
        print >> ofi, r"      end"
        print >> ofi, r"    else"
        print >> ofi, r"      Result := False"
        print >> ofi, r"  end;"
        print >> ofi, r"end;"        
        print >> ofi, r""
        print >> ofi, r"function UpdateReadyMemo(Space, NewLine, MemoUserInfoInfo, MemoDirInfo, MemoTypeInfo,"
        print >> ofi, r"  MemoComponentsInfo, MemoGroupInfo, MemoTasksInfo: String): String;"
        print >> ofi, r"var"
        print >> ofi, r"  S: String;"
        print >> ofi, r"begin"
        print >> ofi, r"  { Fill the 'Ready Memo' with the normal settings and the custom settings }"
        print >> ofi, r"  S := S + MemoDirInfo + NewLine;"
        print >> ofi, r"  S := S + Space + DataDirPage.Values[0] + ' (Data files)' + NewLine + NewLine;"
        print >> ofi, r"  S := S + MemoGroupInfo + NewLine + NewLine;"
        print >> ofi, r"  S := S + MemoTasksInfo + NewLine + NewLine;"
        print >> ofi, r"  Result := S;"
        print >> ofi, r"end;"
        print >> ofi, r""
        print >> ofi, r"procedure CurStepChanged(CurStep: TSetupStep); "
        print >> ofi, r"var"
        print >> ofi, r"  ResultCode: Integer;"
        print >> ofi, r"begin"
        print >> ofi, r"  if CurStep = ssPostInstall then"
        print >> ofi, r"    begin"
        print >> ofi, r"    if not RegKeyExists(HKLM, 'SOFTWARE\Classes\.htm\PersistentHandler') then "
        print >> ofi, r"      {There is no IFilter registered for HTML files; this usually occurs on Windows 2000 Server}"
        print >> ofi, r"      begin"
        print >> ofi, r"      if MsgBox('There is no IFilter registered for HTML files; this will mean you cannot build indexes of these files. Do you want to try and register the default handler?',mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES then"
        print >> ofi, r"        begin"
        print >> ofi, r"        if not Exec( ExpandConstant('{sys}\regsvr32.exe'),ExpandConstant('{sys}\nlhtml.dll'), '', SW_SHOW,ewWaitUntilTerminated, ResultCode) then"
        print >> ofi, r"          MsgBox(SysErrorMessage(ResultCode),mbError, MB_OK)"
        print >> ofi, r"        end;"
        print >> ofi, r"      end;"
        print >> ofi, r"    if not RegKeyExists(HKLM, 'SOFTWARE\Classes\.rtf\PersistentHandler') then "
        print >> ofi, r"      {There is no IFilter registered for RTF files; this usually occurs on Windows 2000}"
        print >> ofi, r"      MsgBox('There is no IFilter registered for RTF files; this will mean you cannot build indexes of these files. You can download the free IFilter from the Microsoft website - see the FAQ for details.', mbInformation, MB_OK);"
        print >> ofi, r"    if not RegKeyExists(HKLM, 'SOFTWARE\Adobe\PDF IFilter 6.0') then "
        print >> ofi, r"      {There is no IFilter registered for PDF files; this usually occurs on machines with no Acrobat installed}"
        print >> ofi, r"      MsgBox('You may not have the correct IFilter installed for PDF files; this may mean you cannot build indexes of these files. You can download the free IFilter from the Adobe website - see the FAQ for details.', mbInformation, MB_OK);"
        print >> ofi, r"    end;"
        print >> ofi, r"end;"
        
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
import getsvnrev
rev = getsvnrev.get_svn_rev()
getsvnrev.gen_revision_file(rev)

import version
from py2exe.build_exe import py2exe


class build_installer(py2exe):
    # This class creates a Windows installer.
    # You need InnoSetup for it.
    def run(self):
        # First, let py2exe do it's work.
        py2exe.run(self)
        
        # create the Installer, using the files py2exe has created.
        script = InnoScript(name="Flax Basic",
                            this_dir=os.getcwd(),
                            versionA=version.get_major(),
                            versionB=version.get_minor(),
                            versionC=version.get_revision(),
                            versionD=version.get_svn(),
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
        self.version = version.get_version_string()
        self.company_name = "Lemur Consulting Ltd"
        self.copyright = "Copyright (c) Lemur Consulting Ltd 2007"
        self.name = "Flax Basic"
# a NT service, modules is required
flaxservice = Target(
    # used for the versioninfo resource
    description = "Flax Basic",
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
                ("static/js/MochiKit",
                glob.glob('../src/static/js/MochiKit/*.js')),
                
                ],

    # targets to build
    console = ["../src/startflax.py"],
    service = [flaxservice],
    # use out build_installer class as extended py2exe build command
    cmdclass = {"py2exe": build_installer},
    )
