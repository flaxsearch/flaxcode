import os
import sys

def setup_sys_path():
    sys.path =  [os.path.normpath(os.path.join(__file__, '..', '..','libs', 'xappy'))]+sys.path
