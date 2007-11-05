import unittest
import os
import sys
import tempfile

sys.path = [os.path.normpath(os.path.join(__file__, '..', '..'))]+sys.path
import setuppaths
sys.path = [os.path.normpath(os.path.join(__file__, '..', '..', 'indexserver'))]+sys.path
import indexer
import flax
import xappy
import flaxpaths

class TestFileTypes(unittest.TestCase):

    def setUp(self):
        flax.options = flax.make_options()
        flaxpaths.paths.dbs_dir = tempfile.mkdtemp()
        self.col = flax.options.collections.new_collection('foo')
        self.col.update(paths = ['sampledocs/issue72'], formats = ['htm', 'html'])
        self.indexserver = indexer.IndexServer()
        self.indexserver.do_indexing(self.col)

    def testFileTypeSearch(self):
        conn = xappy.SearchConnection(self.col.dbpath())

        # not sure why the search below fails to produce any results,
        # bar.htm has 'htm' in the filetype field:
        bar = conn.get_document(os.path.realpath('sampledocs/issue72/bar.htm'))
        print bar.data['filetype']

        res = conn.search(conn.query_parse('filetype:htm'), 0 , 10)
        results = [r for r in res]
        self.assertEqual(len(results), 1)

if __name__ == '__main__':
    unittest.main()

