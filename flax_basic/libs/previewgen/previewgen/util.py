import sys

def is_windows():
    "Determine if we are running under some windows flavour"
    return (sys.platform == "win32")

def find_OOo_paths():
    """Return the paths that need to be added to sys.path in order to
    import pyuno.

    """
    if not is_windows():
        return []
    #FIXME look this up in the registry
    return ['c:/Program Files/OpenOffice.org 3/Basis/program']

def setup_sys_path():
    sys.path = sys.path + find_OOo_paths()
