@echo off
echo Stopping and removing Flax service...
net stop flaxservice
echo Removing Flax service...
flaxservice -remove
sleep 3
echo ..removed


