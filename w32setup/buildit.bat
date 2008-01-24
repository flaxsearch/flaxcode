rem A simple batch file to ease building a fresh version of Flax
cd ..
python utils/install_dependencies.py
cd w32setup
rd dist /s /q
rd build /s /q
python setup_svc.py py2exe
pause