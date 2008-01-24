rem Build all Flax dependencies, then Flax itself
rem .
rem first make sure the Visual C++ environment is set up correctly 
call setupvc.bat
cd ..\libs\xappy\libs
python get_xapian.py
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
nmake check
if errorlevel 0 goto cont2
echo ERROR: could not build Xapian
cd ..\..\..\..\..\
goto end

:cont2
cd ..\..\xapian-bindings\python
nmake check
if errorlevel 0 goto cont3
echo ERROR: could not build Xapian Bindings
cd ..\..\..\..\..\
goto end

:cont3
rem These are necessary to force Distutils to use Visual C++ Express Edition and the Platform SDK
set DISTUTILS_USE_SDK=1
set MSSDK=1
cd ..
python utils/install_dependencies.py
if errorlevel 0 goto cont4
echo ERROR: could not build Flax dependencies
goto end

:cont4
call buildflaxonly.bat
if errorlevel 0 goto cont5
echo ERROR: could not build Flax 
goto end

:cont5
:end
cd w32setup
pause
