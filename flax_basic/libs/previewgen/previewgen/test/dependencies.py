"""

Unit tests for third party programs.


"""

import subprocess
import unittest
import sys
import os


dirname = os.path.dirname(__file__)
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

    def test_ghostscript_present(self):
        subprocess.check_call(["ghostscript", "-v"])
        
