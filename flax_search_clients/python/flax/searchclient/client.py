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
r"""Flax search server client.

"""
__docformat__ = "restructuredtext en"

import urllib
import urllib2
import utils

class Client(object):
    """Client for the Flax search server.

    This client should be used only from a single thread at once.

    The time taken for the last call made is available in the
    `last_elapsed_time` member (this is set to None if not available).

    The version of the API which is being used, and the base url which is being
    used, are available as the `api_version` member and `base_url` member,
    respectively.

    """

    def __init__(self, base_url):
        """Create a client.

        Note that no connection is made to the server until the client is used.

         - `base_url`: The base URL to connect to the server on.  This does not
           include the API version (ie, the "v0" section of the URL).  It need
           not end with a '/' - if it doesn't, one will be added automatically.

        """
        if not base_url.endswith('/'):
            base_url += '/'
        self.base_url = base_url

        self.last_elapsed_time = None
        self.api_version = None

    def __del__(self):
        """Call close explicitly, to allow for tidier clean-up.

        """
        self.close()

    def do_request(self, path, qs=None, data=None):
        """Make a request to the server directly.

        This is not normally used by user code, but is available if you need to
        make a direct request to the server, for some reason.

        """
        if qs is not None:
            args = []
            for field, vals in qs.iteritems():
                if vals is None:
                    continue
                if not hasattr(vals, '__iter__'):
                    vals = [vals]
                vals = filter(None, vals)
                args.append((field, vals))
            path += '?' + urllib.urlencode(args, doseq=1)

        if data is None:
            print(self.base_url + path)
            fd = urllib2.urlopen(self.base_url + path)
        else:
            data = urllib.urlencode(data, doseq=1)
            fd = urllib2.urlopen(self.base_url + path, data)
        res = fd.read()
        fd.close()
        return res

    def close(self):
        # Nothing to clean up, currently.
	# When we support persistent connections, should close the connection.
        pass

    def get_databases(self):
        """Get a tuple containing the names of the databases.

        """
        return tuple(utils.json.loads(self.do_request('dbs')))

    def create_database(self, dbname):
        """Create a database with the given name.

        """
        return self.do_request('dbs/' + utils.quote(dbname))
