rem go3.bat

call setpaths.bat

REM start the Clade classifier on the example data
python classify.py textdir data\socpsy-pages
REM start the Clade UI server - go to http://localhost:8080 to try it
python server.py
