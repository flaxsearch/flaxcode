rem A simple batch file to ease building a fresh version of Flax
cd ..
rem These are necessary to force Distutils to use Visual C++ Express Edition and the Platform SDK
set DISTUTILS_USE_SDK=1
set MSSDK=1
python utils/install_dependencies.py
cd w32setup
rd dist /s /q
rd build /s /q
python setup_svc.py py2exe
pause