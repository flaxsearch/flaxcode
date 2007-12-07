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
        print >> ofi, r"""
; WARNING: This script has been created by py2exe. Changes to this script
; will be overwritten the next time py2exe is run!
[Setup]
AppName=%(name)s
AppVerName=%(name)s PRERELEASE version %(versionA)s.%(versionB)s.%(versionC)s.%(versionD)s
VersionInfoVersion=%(versionA)s.%(versionB)s.%(versionC)s.%(versionD)s
DefaultDirName={pf}\%(name)s
DefaultGroupName=%(name)s
AppPublisher=%(publisher)s
AppPublisherURL=%(homepage)s
AppSupportURL=%(homepage)s
AppUpdatesURL=%(homepage)s
LicenseFile=%(licensefile)s
OutputDir=%(output_dir)s
OutputBaseFilename=setup
Compression=lzma
SolidCompression=yes
SetupIconFile=install.ico
WizardImageFile=install.bmp
WizardSmallImageFile=install_small.bmp
WizardImageStretch=no
WizardImageBackColor=$FFFFFF

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "%(dist_dir)s\startflax.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "%(dist_dir)s\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "%(src_dir)s\cp.conf"; DestDir: "{app}\conf"; Flags: onlyifdoesntexist
Source: "%(src_dir)s\flaxlog.conf"; DestDir: "{app}\conf"; Flags: onlyifdoesntexist
Source: "%(localinst_dir)s\processing\_processing.pyd"; DestDir: "{app}\localinst"; Flags: ignoreversion
Source: "%(localinst_dir)s\htmltotext.pyd"; DestDir: "{app}\localinst"; Flags: ignoreversion
Source: "%(this_dir)s\vcredist_x86.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "%(this_dir)s\startflaxservice.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "%(this_dir)s\stopflaxservice.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "%(this_dir)s\WindowsInstaller-KB893803-v2-x86.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "%(this_dir)s\msvcp71.dll"; DestDir: "{app}\localinst"; Flags: ignoreversion
Source: "%(this_dir)s\zlib1.dll"; DestDir: "{app}\localinst"; Flags: ignoreversion
Source: "%(this_dir)s\exampledocs\*"; DestDir: "{app}\exampledocs"; Flags: ignoreversion
Source: "%(this_dir)s\gettingstarted\*"; DestDir: "{app}\gettingstarted"; Flags: ignoreversion
Source: "%(this_dir)s\*.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "%(this_dir)s\..\docs\reference.html"; DestDir: "{app}\static\docs"; Flags: ignoreversion
Source: "%(this_dir)s\..\docs\*.css"; DestDir: "{app}\static\docs"; Flags: ignoreversion
Source: "%(this_dir)s\..\docs\img\*.png"; DestDir: "{app}\static\docs\img"; Flags: ignoreversion
; NOTE: Do not use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{group}\%(name)s (Manual Start)"; Filename: "{app}\startflax.exe"; IconFilename: "{app}\install.ico"
Name: "{group}\{cm:ProgramOnTheWeb,%(name)s}"; Filename: "http://www.flax.co.uk"
Name: "{group}\Getting Started Guide"; Filename: "file://{app}\gettingstarted\GettingStartedOnWindows.htm"
Name: "{group}\Reference Manual"; Filename: "file://{app}\static\docs\reference.html"
Name: "{group}\{cm:UninstallProgram,%(name)s}"; Filename: "{uninstallexe}"; IconFilename: "{app}\uninstall.ico"
Name: "{commondesktop}\%(name)s"; Filename: "{app}\startflax.exe"; Tasks: desktopicon; IconFilename: "{app}\install.ico"

[Registry]
Root: HKLM; Subkey: "Software\%(publisher)s"; Flags: uninsdeletekeyifempty
Root: HKLM; Subkey: "Software\%(publisher)s\%(name)s"; Flags: uninsdeletekey
Root: HKLM; Subkey: "Software\%(publisher)s\%(name)s\RuntimePath"; ValueType: string; ValueName: ""; ValueData: "{app}"
Root: HKLM; Subkey: "Software\%(publisher)s\%(name)s\DataPath"; ValueType: string; ValueName: ""; ValueData: "{code:GetDataDir}"

[Run]
; Install new Microsoft Installer
Filename: "{app}\WindowsInstaller-KB893803-v2-x86.exe"; StatusMsg: "Installing Microsoft Installer"; Parameters: "-quiet -norestart"; Flags: waituntilterminated shellexec
; Install Visual C++ dependencies
Filename: "{app}\vcredist_x86.exe"; StatusMsg: "Installing Microsoft dependencies"; Parameters: "-q"; Flags: waituntilterminated shellexec
; Set admin password
Filename: "{app}\startflax.exe"; StatusMsg: "Setting administration password"; Parameters: "--set-admin-password"; Flags: waituntilterminated
; Install & run Service
Filename: "{app}\startflaxservice.bat"; Description: "{cm:LaunchProgram,%(name)s as a Windows Service}"; Flags: postinstall waituntilterminated
Filename: "{app}\gettingstarted\GettingStartedOnWindows.htm"; Description: "Read the Getting Started guide"; Flags: postinstall shellexec

[Dirs]
Name: {code:GetDataDir}; Flags: uninsneveruninstall

[Code]
var
DataDirPage: TInputDirWizardPage;
LightMsgPage: TOutputMsgWizardPage;

function InitializeSetup(): Boolean;
begin
{ Check if our registry key exists, in which case assume we're already installed }
if RegKeyExists(HKLM, 'Software\%(publisher)s\%(name)s') then begin
    MsgBox('%(name)s:'#13#13'Flax is already installed. Please uninstall the previous version before installing this version.'#13#13'There is an option to uninstall in Start, Programs, %(name)s', mbError, MB_OK);
    Result := False;
  end else
    Result := True;
end;

procedure InitializeWizard;
begin
{ Create the pages }

DataDirPage := CreateInputDirPage(wpSelectDir,
    'Select Data Directory', 'Where should data files be stored?',
    'Select the folder in which %(name)s should store its data files, then click Next. '#13#13 +
    'Note that Flax data files can be very large, so you may want to store them on a separate ' +
    'disk or partition.',
    False, '');
DataDirPage.Add('');

LightMsgPage := CreateOutputMsgPage(wpPreparing,
    'Set Administration Password', 'Set Administration Password',
    'After installation, Setup will ask you to enter a password for the Administration pages of %(name)s.'#13#13 +
    'To view these pages you will need to use a username of ' + '"admin"' + ' and the password you choose. '#13#13 +
    'You will be asked to confirm the password by typing it twice.');

end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
I: Integer;
begin
{ Validate certain pages before allowing the user to proceed }
if CurPageID = wpSelectDir then begin
    { Set initial value }
    DataDirPage.Values[0] := ExpandConstant('{app}\Data')
    end;
if CurPageID = DataDirPage.ID then begin
if DataDirPage.Values[0] = '' then
    DataDirPage.Values[0] := ExpandConstant('{app}\Data')
    Result := True;
    end;
Result := True;
end;

function GetDataDir(Param: String): String;
begin
{ Return the selected DataDir }
Result := DataDirPage.Values[0];
end;

function InitializeUninstall(): Boolean;
{ Ask the user if they want to uninstall everything }
var
SetDataPath: String;
ResultCode: Integer;
AlreadyStoppedSvc: Boolean;
begin
  AlreadyStoppedSvc := False;
  if MsgBox('Do you want to remove ALL %(name)s data - be careful, this includes settings and all indexes! Click No if you are upgrading to a newer version of %(name)s',mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES then begin
    { First stop the service, so we can delete files }
    Exec(ExpandConstant('{app}\stopflaxservice.bat'), '', '', SW_SHOW,ewWaitUntilTerminated, ResultCode);
    AlreadyStoppedSvc := True;
    DelTree(ExpandConstant('{app}')+'\conf',True,True,True);
    DelTree(ExpandConstant('{app}')+'\var',True,True,True);
    DelTree(ExpandConstant('{app}')+'\logs',True,True,True);
    if RegKeyExists(HKLM, 'Software\%(publisher)s\%(name)s') then
       if RegQueryStringValue(HKEY_LOCAL_MACHINE, 'Software\%(publisher)s\%(name)s\DataPath','', SetDataPath) then
         DelTree(SetDataPath,True,True,True);
  end;
  if AlreadyStoppedSvc then
    Result:=True
  else begin
    { We have to ask if they're going on to remove the program as if so, and we haven't stopped the svc, we should }
    if MsgBox('Do you want to remove the %(name)s program? Click Yes if you are upgrading to a newer version of %(name)s',mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES then begin
      Exec(ExpandConstant('{app}\stopflaxservice.bat'), '', '', SW_SHOW,ewWaitUntilTerminated, ResultCode);
      Result := True;
      end
    else
      Result := False
  end;
end;

function UpdateReadyMemo(Space, NewLine, MemoUserInfoInfo, MemoDirInfo, MemoTypeInfo,
  MemoComponentsInfo, MemoGroupInfo, MemoTasksInfo: String): String;
var
  S: String;
begin
  { Fill the 'Ready Memo' with the normal settings and the custom settings }
  S := S + MemoDirInfo + NewLine;
  S := S + Space + DataDirPage.Values[0] + ' (Data files)' + NewLine + NewLine;
  S := S + MemoGroupInfo + NewLine + NewLine;
  S := S + MemoTasksInfo + NewLine + NewLine;
  Result := S;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
begin
  if CurStep = ssPostInstall then
    begin
    if not RegKeyExists(HKLM, 'SOFTWARE\Classes\.htm\PersistentHandler') then
      {There is no IFilter registered for HTML files; this usually occurs on Windows 2000 Server}
      begin
      if MsgBox('There is no IFilter registered for HTML files; this will mean you cannot build indexes of these files. Do you want to try and register the default handler?',mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES then
        begin
        if not Exec( ExpandConstant('{sys}\regsvr32.exe'),ExpandConstant('{sys}\nlhtml.dll'), '', SW_SHOW,ewWaitUntilTerminated, ResultCode) then
          MsgBox(SysErrorMessage(ResultCode),mbError, MB_OK)
        end;
      end;
    if not RegKeyExists(HKLM, 'SOFTWARE\Classes\.rtf\PersistentHandler') then
      {There is no IFilter registered for RTF files; this usually occurs on Windows 2000}
      MsgBox('There is no IFilter registered for RTF files; this will mean you cannot build indexes of these files. You can download the free IFilter from the Microsoft website - see the FAQ for details.', mbInformation, MB_OK);
    if not RegKeyExists(HKLM, 'SOFTWARE\Adobe\PDF IFilter 6.0') then
      if not RegKeyExists(HKLM, 'SOFTWARE\Adobe\Acrobat Reader') then
        {There is no IFilter registered for PDF files; this usually occurs on machines with no Acrobat installed}
        MsgBox('You may not have the correct IFilter installed for PDF files; this may mean you cannot build indexes of these files. You can download the free IFilter from the Adobe website - see the FAQ for details.', mbInformation, MB_OK);
    end;
end;
""" % self.__dict__
        
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
