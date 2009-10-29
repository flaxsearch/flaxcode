""" Creates an openoffice service on the local machine. This only
needs to be run once.

You need the windows server 2003 resource kit tools installed (a free
download from MS).

Obviously you need openoffice.

"""

import subprocess
import _winreg

reskit_root = "C:\\Program Files\\Windows Resource Kits\\Tools\\"
instsrv =  reskit_root + 'instsrv.exe'
srvany = reskit_root + 'srvany.exe'

ooo_servicename = "oooservice"
ooo_command_line = r'"C:\Program Files\OpenOffice.org 3\program\soffice.exe" -headless -nofirststartwizard -accept="socket,host=localhost,port=8100;urp;StarOffice.Service"'

def make_service(servicename, commandline):
    subprocess.check_call([instsrv, servicename, srvany])

    # if we get this far the registry entry will be created. We now need
    # to tell it what to actually run

    service_key_name = r"SYSTEM\CurrentControlSet\Services\\" + servicename

    with _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, service_key_name) as reg:
        with  _winreg.CreateKey(reg, "Parameters") as k:
            _winreg.SetValue(
                k, "Application", _winreg.REG_SZ,
                commandline)

make_service(ooo_servicename, ooo_command_line)

