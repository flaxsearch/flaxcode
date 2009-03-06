rem Build Flax
rd dist /s /q
rd build /s /q
python setup_svc.py py2exe
pause