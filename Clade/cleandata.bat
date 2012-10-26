REM remove all data from Clade

call setpaths.bat

del %SOLRPATH%\example\solr\data /q /s
rd %SOLRPATH%\example\solr\data\index
rd %SOLRPATH%\example\solr\data\spellchecker
rd %SOLRPATH%\example\solr\data
