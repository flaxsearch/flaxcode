#!/usr/bin/env python
#
# Copyright (C) 2007 Lemur Consulting Ltd
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
r"""test.py: Test htmltotext module.

"""

import unittest
import htmltotext

class TestHtmlToText(unittest.TestCase):

    def test_default_charset(self):
        """Test a conversion supplying a string, which should use the default
        character set.
        
        """
        html = '<title>foo\xa3</title>'
        self.assertEqual(htmltotext.extract(html).title, u'foo\xa3')

    def test_unicode_input(self):
        """Test supplying a unicode string as input.

        """
        html = u'<meta http-equiv="content-type" content="charset=latin1"/><title>foo\xa3</title>'
        self.assertEqual(htmltotext.extract(html).title, u'foo\xa3')

    def test_meta_content_type(self):
        """Test supplying a meta http-equiv tag to set the character set.

        """
        html = '<meta http-equiv="content-type" content="charset=utf8"/><title>foo\xc2\xa3</title>'
        self.assertEqual(htmltotext.extract(html).title, u'foo\xa3')

    def test_meta_content_type(self):
        """Test supplying a meta http-equiv tag to set the character set
        incorrectly.

        Will raise an error when trying to convert the output to unicode.

        """
        html = '<meta http-equiv="content-type" content="charset=utf8"/><title>foo\xa3</title>'
        self.assertEqual(htmltotext.extract(html).title, u'foo')
        self.assertEqual(htmltotext.extract(html).badly_encoded, True)

    def test_meta_description(self):
        """Test supplying a meta description tag.

        """
        html = '<meta name="description" content="desc"/><title>foo</title><body>body</body>'
        self.assertEqual(htmltotext.extract(html).title, u'foo')
        self.assertEqual(htmltotext.extract(html).sample, u'desc')
        self.assertEqual(htmltotext.extract(html).keywords, u'')
        self.assertEqual(htmltotext.extract(html).indexing_allowed, True)
        self.assertEqual(htmltotext.extract(html).badly_encoded, False)

    def test_meta_description(self):
        """Test supplying a meta description tag.

        """
        html = '<meta name="robots" content="noindex"/><title>foo</title><body>body</body>'
        self.assertEqual(htmltotext.extract(html).title, u'')
        self.assertEqual(htmltotext.extract(html).sample, u'')
        self.assertEqual(htmltotext.extract(html).keywords, u'')
        self.assertEqual(htmltotext.extract(html).indexing_allowed, False)

def suite():
    return unittest.makeSuite(TestHtmlToText)

def test():
    runner = unittest.TextTestRunner()
    runner.run(suite())

if __name__ == '__main__':
    test()

