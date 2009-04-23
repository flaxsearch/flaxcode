# Copyright (c) 2009 Lemur Consulting Ltd
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Backend support.

Backends are lazily loaded when first accessed.

"""
__docformat__ = "restructuredtext en"

# Global modules
import os
import threading
import wsgiwapi

# All operations which check for a specific backend, or 
_backend_load_mutex = threading.Lock()

# The backends which are defined.
# We could just allow any backend which import finds to be used, but this might
# be insecure, and certainly harder to audit for security - any module on the
# python path which ends with _backend could be imported.
allowed_backends = set(('xappy', 'whoosh', ))

# The backends which have been imported.
# This shouldn't be accessed without holding _backend_load_mutex.
_active_backends = {}

def check_backend_settings(backend_settings):
    """Check that the backend settings supplied are valid.

    Raise NotImplementedError if any of the keys in backend_settings are not
    the name of a valid backend.

    """
    for backend_name in backend_settings.keys():
        if backend_name not in allowed_backends:
            raise NotImplementedError("Backend '%r' (mentioned in settings) is not a supported backend" % backend_name)

def get_backends():
    """Get a list of the backends in use.

    The list will be in sorted alphabetical order.

    """
    _backend_load_mutex.acquire()
    try:
        result = list(item for item in _active_backends.iteritems())
        result.sort()
        return result
    finally:
        _backend_load_mutex.release()

def get(backend_name, backend_settings):
    """Get a Backend object for the specified backend.

     - `backend_name` is the name of the backend in use.
     - `backend_settings` is a dictionary of backend-specific settings to use,
       keyed by backend name.

    If the backend is not an allowed backend (either because it is not known,
    or because the necessary supporting modules cannot be imported) a 400 error
    will be raised.  Otherwise, the Backend object for the specified backend
    name is returned.

    """

    # First, check for the backend without the lock (once the backend is set,
    # it doesn't change, and Python provides sufficient guarantees that it's
    # safe to try looking in _active_backends at any time).
    backend = _active_backends.get(backend_name)
    if backend is not None:
        return backend

    # Check that the backend name is allowed.
    if backend_name not in allowed_backends:
        raise wsgiwapi.HTTPError(400, "Backend '%s' not known" % backend_name)

    _backend_load_mutex.acquire()
    try:
        # Check for the backend again now we have the mutext, to avoid race
        # conditions where backend is created by another thread between the
        # first check and acquiring the lock.
        backend = _active_backends.get(backend_name)
        if backend is not None:
            return backend

        # Try importing the backend module.
        try:
            Backend = __import__('flax.searchserver.backends.' + backend_name + '_backend',
                                     globals(), locals(), ['Backend','Database']).Backend
        except ImportError, e:
            raise wsgiwapi.HTTPError(400, "Backend '%s' not supported" % backend_name)

        # Make the backend object, register it and return it.
        backend = Backend(backend_settings.get(backend_name, {}))
        _active_backends[backend_name] = backend
        return backend
    finally:
        _backend_load_mutex.release()
