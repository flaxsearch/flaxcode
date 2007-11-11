# quite a few pdfs seem to raise com errors when filtering with
# ifilter (i.e. the adobe IFilter) for reasons that are not entirely
# clear.

import unittest
import os
import sys
import logging
logging.basicConfig(level=logging.DEBUG)

sys.path.append('..')
sys.path.append('../indexserver')
import w32com_ifilter
class TestPdfFilter(unittest.TestCase):

    def testFilterukpga_19960008_en_pdf(self):
        fname = os.path.join(os.path.realpath('sampledocs'), 'problem_docs', 'ukpga_19960008_en.pdf')
        stuff = list(w32com_ifilter.ifilter_filter(fname))

    def testRepeatRemoteFiltering(self):
        """this file error - here we repeatedly try to filter it catching the
        error, the remote filter should make a new process each time
        the error occurs.
        """
        fname = os.path.join(os.path.realpath('sampledocs'), 'problem_docs', 'ukpga_19960008_en.pdf')
        for i in xrange(100):
            try:
                stuff = list(w32com_ifilter.remote_ifilter(fname))
            except:
                pass

if __name__ == '__main__':
    unittest.main()

    
