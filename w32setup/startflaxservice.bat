@echo off
echo Installing and starting Flax service...
flaxservice -install -auto
net start flaxservice
sleep 3
echo ..started


