rem *********************
rem * One way of starting Open Office in windows using a batch file
rem *********************
rem Note the -invisible option is necessary to prevent a few random popups from OO!
rem -headless is apparently a hack, and will eventually go away.

"C:\Program Files\OpenOffice.org 3\program\soffice.exe" -headless -invisible -nofirststartwizard -accept="socket,host=localhost,port=8100;urp;StarOffice.Service"