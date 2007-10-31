@echo off
rem Batch file for making all Win32 targets for Flax
rem Makes various files in the dist/ folder using Python distutils and py2exe to convert these into a standalone
rem that doesn't need Python to be installed. 
rem Then uses InnoSetup to create a Windows installer from these files. 
echo ****** Creating Windows Installer for Flax..
setlocal
path=C:\Program Files\Inno Setup 5;%path%
echo ****** Removing old files..
rd dist /q/s

rem Get rid of any compiled Python
del /q *.pyc 
cd ..\src
del /q /s *.pyc 

rem Install the dependencies
cd ..
echo ****** Installing Flax dependencies..
python utils/install_dependencies.py
if not errorlevel 0 goto fail
copy \work\xapian-svn\xapian-core\win32\release\Python\xapian.py C:\Python25\lib\site-packages
if not errorlevel 0 goto fail

rem Do the distutils script...
cd w32setup
echo ****** Running Python Setup..
python setup_svc.py py2exe 
if not errorlevel 0 goto fail

rem  Bring in some files Py2exe missed
echo ****** Copying extra files
cd dist
copy ..\..\localinst\processing\_processing.pyd
copy ..\..\localinst\htmltotext.pyd 
copy \windows\msvcr80.dll 
copy \windows\system32\msvcp71.dll 
copy ..\zlib1.dll
copy ..\stopflaxservice.bat
copy ..\startflaxservice.bat
rem Get Xapian
copy \work\xapian-svn\xapian-core\win32\release\Python\_xapian.pyd
if not errorlevel 0 goto fail

rem  Build the installer package
cd ..
echo ****** Running InnoSetup..
compil32 /cc flax.iss
if not errorlevel 0 goto fail
echo ****** ..Windows Installer created.
goto end

:fail
echo ****** FAILED ******
:end