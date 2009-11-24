import setuppaths
import os
import multiprocessing
import cherrypy
import win32serviceutil
import win32service


# once the service is created it'll need permissions to write the log
# files.  Either change the permissions on the log files, or change
# the user that the service runs as to one that can write the log files.

# Also it'll need permissions to read all the document
# collections. This can particularly be an issue with network
# drives. Again - either change the permissions or the user that the
# service runs as.

#need to patch multiprocessing - see http://bugs.python.org/issue5162

import startflax

class FlaxService(win32serviceutil.ServiceFramework):
    """NT Service."""
    
    _svc_name_ = "FlaxService"
    _svc_display_name_ = "FlaxService"

    def SvcDoRun(self):


        this_dir=os.path.dirname(os.path.abspath(__file__))
        opts = startflax.StartupOptions(
            main_dir=os.path.join(this_dir, 'data'),
            src_dir=this_dir,
            dbs_dir=os.path.join(this_dir, 'data', 'dbs'),
            log_dir=os.path.join(this_dir, 'data', 'logs'),
            conf_dir=this_dir,
            var_dir=os.path.join(this_dir, 'data', 'var'))
        self.main = startflax.FlaxMain(opts)
        self.main.start(blocking=True)
                
    def SvcStop(self):
        self.main.stop()
        self.main.join()


if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(FlaxService)
