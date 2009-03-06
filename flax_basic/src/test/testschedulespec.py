from __future__ import with_statement
import unittest
import sys
import os
sys.path = [os.path.normpath(os.path.join(__file__, '..', '..'))]+sys.path
import schedulespec
import datetime

class TestFileSpec(unittest.TestCase):

    def testIssue150(self):
        # http://code.google.com/p/flaxcode/issues/detail?id=150
        ss = schedulespec.ScheduleSpec()
        ss.mins = ss.monthdays = ss. months = ss._wildcard
        ss.weekdays=[3]
        ss.hours=[2]
        t = datetime.datetime(2007, 11, 29, 2)
        self.assert_(ss.matching_time(t))

            
if __name__ == '__main__':
    unittest.main()
