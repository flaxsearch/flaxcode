@echo off
echo Installing and starting Flax service...
flaxservice -install -auto
if errorlevel = 0 goto next
goto error
:next
net start flaxservice
if errorlevel = 0 goto next2
goto error
:next2
rem this is a way of waiting for 5 seconds on Windows 2000 upwards
@ping 127.0.0.1 -n 2 -w 1000 > nul
@ping 127.0.0.1 -n 5 -w 1000> nul

echo ..started
exit
:error
echo ERROR! Could not start Flax service!


