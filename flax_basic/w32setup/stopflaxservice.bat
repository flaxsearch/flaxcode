@echo off
echo Stopping and removing Flax service...
net stop flaxservice
if errorlevel = 0 goto next
goto error
:next
echo Removing Flax service...
flaxservice -remove
if errorlevel = 0 goto next2
goto error
:next2
rem this is a way of waiting for 6 seconds on Windows 2000 upwards
@ping 127.0.0.1 -n 2 -w 1000 > nul
@ping 127.0.0.1 -n 6 -w 1000> nul

echo ..removed
exit
:error
echo ERROR! Could not stop and remove Flax service!
