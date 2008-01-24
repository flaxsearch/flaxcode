rem Build all Flax dependencies, then Flax itself
rem .
rem first make sure the Visual C++ environment is set up correctly 
call setupvc.bat
cd ..\libs\xappy\libs
rem python get_xapian.py
if errorlevel 0 goto cont1
echo ERROR: could not get the latest Xapian
cd ..\..\..\
goto end

:cont1
cd xapian-core/win32
cd makedepend
nmake -f makedepend.mak
copy makedepend.exe ..
cd ..
rem nmake check
nmake
if errorlevel 0 goto cont2
echo ERROR: could not build Xapian
cd ..\..\..\..\..\
goto end

:cont2
cd ..\..\xapian-bindings\python
rem nmake check
nmake
if errorlevel 0 goto cont21
echo ERROR: could not build Xapian Bindings
cd ..\..\..\..\..\
goto end

:cont21
cd ..\..\xapian-core\win32\release\Python
del C:\Python25\lib\site-packages\xapian.*
del C:\Python25\lib\site-packages\_xapian.*
copy xapian.py C:\Python25\lib\site-packages
copy _xapian.pyd C:\Python25\lib\site-packages
cd ..\..\..\..\..\..\..

:cont3
rem These are necessary to force Distutils to use Visual C++ Express Edition and the Platform SDK
set DISTUTILS_USE_SDK=1
set MSSDK=1
python utils/install_dependencies.py
rem Must wedge a manifest into the processing tool, otherwise it won't load the VC library correctly
cd localinst/processing
mt.exe -outputresource:_processing.pyd;#2 -manifest _processing.pyd.manifest
cd ..
mt.exe -outputresource:htmltotext.pyd;#2 -manifest htmltotext.pyd.manifest
cd ..
if errorlevel 0 goto cont4
echo ERROR: could not build Flax dependencies
goto end

:cont4
cd w32setup
call buildflaxonly.bat
if errorlevel 0 goto cont5
echo ERROR: could not build Flax 
goto end

:cont5
:end
cd w32setup
pause
