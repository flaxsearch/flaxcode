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
r"""Test creation and deletion of databases

"""
__docformat__ = "restructuredtext en"

from testsettings import *

class DbCreateTest(unittest.TestCase):
    def setUp(self):
        self.client = Client(baseurl)

    def tearDown(self):
        self.client.close()

    def test_create_and_delete(self):
        """Test creating and deleting a database.

        """
        sillydbname = u'db1/with:a:stupi\u0256 name!\'"/'
        sillydbname = u'db1'

        self.client.delete_database(sillydbname, allow_missing=True)
        self.assertTrue('db1' not in self.client.get_databases())
        self.client.create_database(sillydbname)
        self.assertTrue('db1' in self.client.get_databases())
        self.client.delete_database(sillydbname)
        self.assertTrue('db1' not in self.client.get_databases())

    def test_basicadd1(self):
        """Test basic adding of documents.

        """
	dbname = 'db1'
        self.client.delete_database(dbname, allow_missing=True)
        self.client.create_database(dbname)
        db = self.client.db(dbname)

	self.assertEqual(db.doccount, 0)

        self.client.delete_database(dbname)

if __name__ == '__main__':
    main()
