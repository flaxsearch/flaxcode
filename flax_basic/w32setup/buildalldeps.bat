rem Build all Flax dependencies, then Flax itself
rem .
rem first make sure the Visual C++ environment is set up correctly 


call setupvc.bat
if (%1) == (nobindings) goto cont3
cd ..\libs\xappy\libs
call build_xapian_win32.bat 26
if errorlevel 0 goto cont21
echo ERROR: could not build Xapian python bindings
cd ..\..\..\
goto end

:cont21
cd ..\..\xapian-core\win32\release\Python
del C:\Python26\lib\site-packages\xapian.*
del C:\Python26\lib\site-packages\_xapian.*
copy xapian.py C:\Python26\lib\site-packages
copy _xapian.pyd C:\Python26\lib\site-packages
cd ..\..\..\..\..\..\..

:cont3
rem These are necessary to force Distutils to use Visual C++ Express Edition and the Platform SDK
set DISTUTILS_USE_SDK=1
set MSSDK=1
python ../utils/install_dependencies.py
if errorlevel 0 goto cont31
echo ERROR: could install Flax dependencies
goto end

:cont31
rem Must wedge a manifest into processing and htmltotext, otherwise they won't load the VC library correctly
cd ../localinst/processing
mt.exe -outputresource:_processing.pyd;#2 -manifest _processing.pyd.manifest
cd ..
rem TODO check whether this one is needed!
mt.exe -outputresource:htmltotext.pyd;#2 -manifest htmltotext.pyd.manifest
cd ..
if errorlevel 0 goto cont4
echo ERROR: could not build Flax dependencies
goto end

:cont4
rem install Xappy so our setup_svc.py will pick it up later
cd libs\xappy
python setup.py install
if errorlevel 0 goto cont41
echo ERROR: could not install xappy
goto end
:cont41
rem install htmltotext so our setup_svc.py will pick it up later
cd ..\..\libs\htmltotext
python setup.py install
if errorlevel 0 goto cont42
echo ERROR: could not install htmltotext
goto end
:cont42
rem build Flax itself
cd ..\..\w32setup
call buildflaxonly.bat
if errorlevel 0 goto cont5
echo ERROR: could not build Flax 
goto end

:cont5
:end
cd w32setup
pause
