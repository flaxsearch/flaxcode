import copy
import os
import sys

import settings
import util

def setup_sys_path():
    #assume that linux distributions get it right.
    if util.is_windows():
        sys.path = sys.path + settings.ooo_python_paths


def fixup_ooo_environ():
    """On windows using uno is tricky since it really expects to be
    run using the version of python shipped with Ooo. Calling this
    should fix things, but note that you still need to be binary
    compatible (probably exactly the same version of python). If you
    want to use a different version of python you will need to rebuild
    the pyuno module.

    """
    if util.is_windows():
        os.environ['PATH'] = os.environ['PATH'] + settings.ooo_environment_PATH
        url = copy.copy(settings.ooo_environment_URE_BOOTSTRAP)
        url = url.replace(' ', '%20')
        url = 'file:///'+url
        os.environ['URE_BOOTSTRAP'] = url

def setup():
    setup_sys_path()
    fixup_ooo_environ()
    
