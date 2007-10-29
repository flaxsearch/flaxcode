from __future__ import with_statement
import unittest
import os
import shutil
import sys
import tempfile

sys.path = [os.path.normpath(os.path.join(__file__, '..', '..'))]+sys.path
import filespec


class TestFileSpec(unittest.TestCase):

    def setUp(self):
        subdirs = ['foo', 'bar']
        self.dirname = tempfile.mkdtemp()
        for dir in subdirs:
            dname = os.path.join(self.dirname, dir)
            os.mkdir(dname)
            with open(os.path.join(dname, "foo.txt"), 'w') as f:
                f.write("Hello World")
        
    def testbasic(self):
        fs = filespec.FileSpec()
        fs.update(paths = [self.dirname], formats = ['txt'])
        self.assertEqual(set(fs.files()),
                         set((os.path.join(self.dirname, 'foo', 'foo.txt'),
                              os.path.join(self.dirname, 'bar', 'foo.txt'))))

if __name__ == '__main__':
    unittest.main()
