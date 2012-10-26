rem go1.bat

REM call some helper batch files that add paths to Python and Java
call \work\py27.bat
call \work\java6.bat
REM import the example data
python classify.py import data\socpsy.csv
REM copy Clade's SOLR configuration to the Solr folder (modify the latter as per your installation of SOLR)
copy solr-conf\*.* \work\tools\apache-solr-3.6.0\example\solr\conf /Y
REM go there and start SOLR
cd \work\tools\apache-solr-3.6.0\example
java -jar start.jar &