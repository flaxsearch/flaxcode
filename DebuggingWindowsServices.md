# Introduction #

When running Flax (or any Python program) as a Windows Service it is often very difficult to know what is happening due to the redirection of stderr and stdout to files - any debug prints will usually vanish into the ether, or only become apparent **if** the program exits cleanly. This document explains how to insert code to output debug messages to the Windows Event Log (Control Panel, Administrative Tools, Event Viewer, Applications).

# Details #

Add the following code to the start of a module:

`import servicemanager`

You can then simply output debug as follows:

`servicemanager.LogInfoMsg(' A debug message with a value %s' % someValue)`

The 'processing' module uses a system of debug prints throughout the code as follows:

```
VERBOSE = False

def debug(s):
    if VERBOSE:
        print >>sys.stderr, 'DEBUG [%s] %s' % (_current_process._name, s)
def info(s):
    print >>sys.stderr, '[%s] %s' % (_current_process._name, s)
```
We can add to this as follows:
```
VERBOSE = False
WINSERVICE = False

def debug(s):
    if VERBOSE:
        if WINSERVICE:
            LogInfoMsg('DEBUG [%s] %s' % (_current_process._name, s))
        else:
            print >>sys.stderr, 'DEBUG [%s] %s' % (_current_process._name, s)
def info(s):
    if WINSERVICE:
        LogInfoMsg('INFO [%s] %s' % (_current_process._name, s))
    else:
        print >>sys.stderr, '[%s] %s' % (_current_process._name, s)
```

The debugging can be switched on and off by toggling VERBOSE and WINSERVICE.


Charlie