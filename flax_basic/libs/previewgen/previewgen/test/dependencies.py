"""

Unit tests for third party programs.


"""

import subprocess
import unittest
import sys
import os



dirname = os.path.dirname(os.path.abspath(__file__))
datapath = os.path.join(dirname, "data")
parent = os.path.abspath(os.path.dirname(dirname))
sys.path = [parent] + sys.path

class DependeciesTestCase(unittest.TestCase):

    def setUp(self):
        import setup
        setup.setup()

    def test_uno_connection(self):
        import uno_oo_preview
        uno_oo_preview.get_ooo_desktop()

    def test_magicwand_import(self):
        import PythonMagickWand

    def test_ghostscript_found(self):
        """ ImageMagick uses ghostscript to read pdfs - this test
        checks that it can locate ghostscipt.

        """
        import PythonMagickWand
        wand = PythonMagickWand.NewMagickWand()
        doc1 = os.path.join(datapath, "doc1.pdf")
        PythonMagickWand.MagickReadImage(wand, doc1)
        
if __name__ == "__main__":
    unittest.main()
