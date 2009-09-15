import sys

def is_windows():
    "Determine if we are running under some windows flavour"
    return (sys.platform == "win32")

