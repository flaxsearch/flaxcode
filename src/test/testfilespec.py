from __future__ import with_statement
import unittest
import os
import shutil
import sys
sys.path = [os.path.normpath(os.path.join(__file__, '..', '..'))]+sys.path
import filespec


class TestFileSpec(unittest.TestCase):

    dirname = "/tmp/testfilespecdir/"

    def setUp(self):
        subdirs = ['foo', 'bar']
        if os.path.exists(self.dirname):
            shutil.rmtree(self.dirname)
        os.mkdir(self.dirname)
        for dir in subdirs:
            dname = os.path.join(self.dirname, dir)
            os.mkdir(dname)
            with open(os.path.join(dname, "foo.txt"), 'w') as f:
                f.write("Hello World")
                        
            
        
    def testbasic(self):
        fs = filespec.FileSpec([self.dirname])
        print list(fs.files())


        
if __name__ == '__main__':
    unittest.main()
