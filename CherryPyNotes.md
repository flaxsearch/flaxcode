# Introduction #

CherryPy running as a Windows service can be stopped by Windows
events, this is a workaround.

# Details #

After setting up service threads, CherryPy blocks the main thread by
sitting in a time.sleep() loop, polling for shutdown.  When running as
a Windows service (using srvany.exe), this can be broken by a user
shutting down a console, which results in a SIGBREAK being sent to all
services (?)  This can raise an IOError (interrupted system call) in
sleep(), which propagates and ends the process.

It doesn't seem to be possible to ignore SIGBREAK using either the
signal or win32api modules.  Currently the workaround I have used is
to catch and ignore these errors.  The CherryPy bundled with Flax
needs to be patched similarly, unless a neater solution can be found.

Tom