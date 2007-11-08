# quite a few pdfs seem to raise com errors when filtering with
# ifilter (i.e. the adobe IFilter) for reasons that are not entirely
# clear.

import unittest
import os
import sys

sys.path.append('..')
sys.path.append('../indexserver')
import w32com_ifilter
class TestPdfFilter(unittest.TestCase):

    def testFilterukpga_19960008_en_pdf(self):
        fname = os.path.join(os.path.realpath('sampledocs'), 'problem_docs', 'ukpga_19960008_en.pdf')
        stuff = list(w32com_ifilter.ifilter_filter(fname))

if __name__ == '__main__':
    unittest.main()

    
