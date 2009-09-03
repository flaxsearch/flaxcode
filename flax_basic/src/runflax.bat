rem This file is a quick way to start Flax Basic from the command line on Windows. To run it:
rem      1. First make sure you have Python on your PATH 
rem      2. If you already have Flax Basic installed as a Service, you'll need to halt it using 'net stop flaxservice'
rem      3. Then run this file with the command line option --set-admin-password and follow the prompts
rem      4. Then run this file again, and start a browser and navigate to http://localhost:8090
rem      5. CTRL-C should stop the process

python startflax.py --main-dir=data --conf-dir=. --dbs-dir=data\dbs --log-dir=data\logs --var-dir=data\var --src-dir=. %1 %2 %3 %4
