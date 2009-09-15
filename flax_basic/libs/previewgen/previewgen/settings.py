import util

ooo_base_path = 'c:/Program Files/OpenOffice.org 3/'

ooo_python_paths = ['c:/Program Files/OpenOffice.org 3/Basis/program']

ooo_environment_PATH =  (';' + ooo_base_path + 'URE/bin;' +
                          ooo_base_path + 'Basis/Program')

ooo_environment_URE_BOOTSTRAP = ooo_base_path + 'program/fundamental.ini'


ooo_connection_string = (
    "uno:socket,host=localhost,port=8100;urp;StarOffice.ComponentContext")


lib_wand = ('c:/Program Files/ImageMagick-6.5.5-Q16/CORE_RL_wand.dll'
            if util.is_windows()
            else '/usr/lib/libWand.so.10')



try:
    from local_settings import *
except ImportError:
    pass
