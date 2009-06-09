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

import copy
import urllib
import urllib2
import utils

class FlaxError(Exception):
    """Exception thrown when a request failed.

    The HTTP exception returned is available in the httperror method.

    """
    def __init__(self, httperror):
        Exception(self)
        self.httperror = httperror
        self.code = httperror.code
        self.msg = str(httperror)
        self.body = httperror.read()

    def __str__(self):
        return "<FlaxError(%s)>" % (self.body)

    def __repr__(self):
        return "<FlaxError(%r, %r)>" % (self.msg, self.body)

class RequestMethod(urllib2.Request):
    def __init__(self, method, *args, **kwargs):
        self._method = method
        urllib2.Request.__init__(self, *args, **kwargs)

    def get_method(self):
        return self._method

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

        self.version = 1

        self.versioned_base_url = base_url + 'v%d/' % self.version

        self.last_elapsed_time = None
        self.api_version = None

    def __del__(self):
        """Call close explicitly, to allow for tidier clean-up.

        """
        self.close()

    def do_request(self, path, method='GET', queryargs=None, data=None, json=None, content_type=None):
        """Make a request to the server directly.

        This is not normally used by user code, but is available if you need to
        make a direct request to the server, for some reason.

        """
        if queryargs is not None:
            args = []
            for field, vals in queryargs.iteritems():
                if vals is None:
                    continue
                if not hasattr(vals, '__iter__'):
                    vals = [vals]
                vals = filter(None, vals)
                args.append((field, vals))
            path += '?' + urllib.urlencode(args, doseq=1)

        uri = self.versioned_base_url + path
        if json is not None:
            assert data is None
            data = utils.json.dumps(json)
            if content_type is None:
                content_type = 'application/json'
        headers = {}
        if content_type is not None:
            headers['content-type'] = content_type
        req = RequestMethod(method, uri, data, headers=headers)
        try:
            fd = urllib2.urlopen(req)
        except urllib2.HTTPError, e:
            raise FlaxError(e)
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

    def create_database(self, dbname, overwrite=None, reopen=None, backend=None):
        """Create a database with the given name.

        """
        queryargs = {}
        if overwrite is not None:
            queryargs['overwrite'] = int(bool(overwrite))
        if reopen is not None:
            queryargs['reopen'] = int(bool(reopen))
        if backend is not None:
            queryargs['backend'] = backend
        if len(queryargs) == 0:
            queryargs = None
        return self.do_request('dbs/' + utils.quote(dbname), 'POST',
                               queryargs=queryargs)

    def delete_database(self, dbname, allow_missing=True):
        """Create a database with the given name.

        """
        return self.do_request('dbs/' + utils.quote(dbname), 'DELETE',
                        queryargs={'allow_missing': int(bool(allow_missing))})

    def db(self, dbname):
        return Database(self, dbname)

    def schema(self, dbname):
        return Schema(self, dbname)

class Schema(object):
    def __init__(self, client, dbname):
        self._client = client
        self.dbname = dbname
        self._basepath = 'dbs/' + utils.quote(dbname) + '/schema'

    def get(self):
        json = self._client.do_request(self._basepath, 'GET')
        return utils.json.loads(json)

    def add_field(self, fieldname, *args):
        allfieldprops = {}
        def merge_args(old, new):
            for (k, v) in new.iteritems():
                if k not in old:
                    # Add a new entry
                    old[k] = v
                    continue

                if isinstance(v, dict):
                    # Merge recursively if it's a dict
                    assert isinstance(old[k], dict)
                    old[k] = copy.copy(old[k])
                    merge_args(old[k], v)
                else:
                    # Otherwise overwrite
                    old[k] = v

        # merge the args, which should all be dicts
        for fieldprops in args:
            merge_args(allfieldprops, fieldprops)
        uri = self._basepath + '/fields/' + utils.quote(fieldname)
        self._client.do_request(uri, 'PUT', json=allfieldprops)

    def set_template(self, name, template):
        uri = self._basepath + '/templates/' + utils.quote(name)
        self._client.do_request(uri, 'PUT', data=template, content_type='text/javascript')

    def get_template(self, name):
        uri = self._basepath + '/templates/' + utils.quote(name)
        json = self._client.do_request(uri, 'GET')
        return utils.json.loads(json)['template']

class Database(object):
    """

    """
    def __init__(self, client, dbname):
        self._client = client
        self.dbname = dbname
        self._basepath = 'dbs/' + utils.quote(dbname)

    @property
    def info(self):
        json = self._client.do_request(self._basepath, 'GET')
        return utils.json.loads(json)

    @property
    def doccount(self):
        json = self._client.do_request(self._basepath, 'GET')
        return utils.json.loads(json)['doccount']

    def add_document(self, doc, docid=None):
        """Add a document - if the docid is specified, replaces any existing
        one with that id (but doesn't complain if the document doesn't exist).

        """
        uri = self._basepath + '/docs'
        if docid is not None:
            uri += '/' + utils.quote(str(docid))
        return self._client.do_request(uri, 'POST', json=doc)

    def get_document(self, docid):
        """Get the document with the given id.

        """
        uri = self._basepath + '/docs/' + utils.quote(str(docid))
        return utils.json.loads(self._client.do_request(uri, 'GET'))

    def delete_document(self, docid):
         """Delete a document.

         """
         uri = self._basepath + '/docs/' + utils.quote(str(docid))
         return utils.json.loads(self._client.do_request(uri, 'DELETE'))

    def flush(self):
        """Flush pending changes, and block until they're done.

        """
        self._client.do_request(self._basepath + '/flush', 'POST')

    def search_simple(self, searchstring, start_rank=0, end_rank=10,
                      default_op='AND'):
        return SearchResults(self._client.do_request(self._basepath + '/search/simple', 'GET',
                        queryargs={'query': searchstring,
                        'start_rank': start_rank,
                        'end_rank': end_rank,
                        'default_op': default_op,
                        }))

    def search_similar(self, ids, start_rank=0, end_rank=10, pcutoff=0):
        return SearchResults(self._client.do_request(self._basepath + '/search/similar', 'GET',
                        queryargs={'id': ids,
                        'start_rank': start_rank,
                        'end_rank': end_rank,
                        'pcutoff': pcutoff,
                        }))

    def search_template(self, name, **kwargs):
        uri = self._basepath + '/search/template/' + utils.quote(name)
        return SearchResults(self._client.do_request(uri, 'GET', queryargs=kwargs))

    def search_structured(self, query_all='', query_any='', query_none='',
                          query_phrase='', filter=[],
                          start_rank=0, end_rank=10):
        return SearchResults(self._client.do_request(self._basepath + '/search/structured', 'GET',
                             queryargs={'query_all': query_all,
                             'query_any': query_any,
                             'query_none': query_none,
                             'query_phrase': query_phrase,
                             'filter': filter,
                             'start_rank': start_rank,
                             'end_rank': end_rank,
                             }))

class SearchResults(object):
    def __init__(self, json):
        results = utils.json.loads(json)
        self.start_rank = results['start_rank']
        self.end_rank = results['end_rank']

        # Whether there are more matches
        self.more_matches = results['more_matches']

        self.matches_lower_bound = results['matches_lower_bound']
        self.matches_estimated = results['matches_estimated']
        self.matches_upper_bound = results['matches_upper_bound']
        self.matches_human_readable_estimate = results['matches_human_readable_estimate']
        self.results = [SearchResult(result) for result in results['results']]

    def __repr__(self):
        return '<SearchResults(start_rank=%d, end_rank=%d>' % (
                                self.start_rank,
                                self.end_rank,
                                )

class SearchResult(object):
    def __init__(self, values):
        self.db = values['db']
        self.docid = values['docid']
        self.weight = values['weight']
        self.rank = values['rank']
        self.data = values['data']
