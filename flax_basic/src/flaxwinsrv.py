import setuppaths
import os
import multiprocessing
import cherrypy
import win32serviceutil
import win32service


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
