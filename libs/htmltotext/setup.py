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
"""Setup script for htmltotext extension module.

"""

import sys

# FIXME - use some kind of configure step to determine these.
extra_include_dirs='c:\program files\gnuwin32\include'
extra_library_dirs='c:\program files\gnuwin32\lib'

# Use setuptools if we're part of a larger build system which is already using
# it.
if ('setuptools' in sys.modules):
    import setuptools
    from setuptools import setup, Extension
    from setuptools.command.build_ext import build_ext
    using_setuptools = True
else:
    import distutils
    from distutils.core import setup, Extension
    from distutils import sysconfig
    using_setuptools = False

# Customise compiler options.
if using_setuptools:
    try:
        setuptools_build_ext = build_ext.build_extension
        def my_build_ext(self, ext):
            """Remove the -Wstrict-prototypes option from the compiler command.

            This option isn't supported for C++, so we remove it to avoid annoying
            warnings.

            """
            try:
                self.compiler.compiler_so.remove('-Wstrict-prototypes')
            except (AttributeError, ValueError):
                pass
            retval = setuptools_build_ext(self, ext)
            return retval
        build_ext.build_extension = my_build_ext
    except AttributeError:
        pass
else:
    distutils_customize_compiler = sysconfig.customize_compiler
    def my_customize_compiler(compiler):
        """Remove the -Wstrict-prototypes option from the compiler command.

        This option isn't supported for C++, so we remove it to avoid annoying
        warnings.

        """
        retval = distutils_customize_compiler(compiler)
        try:
            compiler.compiler_so.remove('-Wstrict-prototypes')
        except (AttributeError, ValueError):
            pass
        return retval
    sysconfig.customize_compiler = my_customize_compiler

# List of source files 
htmltotext_sources = [
    'src/htmlparse.cc',
    'src/metaxmlparse.cc',
    'src/myhtmlparse.cc',
    'src/pyhtmltotext.cc',
    'src/utf8convert.cc',
    'src/utf8itor.cc',
    'src/xmlparse.cc',
]

# Extra arguments for setup() which we don't always want to supply.
extra_kwargs = {}
if using_setuptools:
    extra_kwargs['test_suite'] = "test.test"

long_description = """
The htmltotext module
=====================

This package was written for a search engine, to allow it to extract the
textual content and metadata from HTML pages.  It tries to cope with
invalid markup and incorrectly specified character sets, and strips out
HTML tags (splitting words at tags appropriately).  It also discards the
contents of script tags and style tags.

As well as text from the body of the page, it extracts the page title,
and the content of meta description and keyword tags.  It also parses
meta robots tags to determine whether the page should be indexed.

The HTML parser used by this module was extracted from the Xapian search
engine library (and specifically, from the omindex indexing utility in
that library).

"""

setup(name = "htmltotext",
      version = "0.6",
      author = "Richard Boulton",
      author_email = "richard@lemurconsulting.com",
      maintainer = "Richard Boulton",
      maintainer_email = "richard@lemurconsulting.com",
      url = "http://code.google.com/p/flaxcode/wiki/HtmlToText",
      #download_url = "http://code.google.com/p/flaxcode/downloads/list?q=htmltotext",
      download_url = "http://flaxcode.googlecode.com/files/htmltotext-0.6.tar.gz",
      description = "Extract text and some metainfo from HTML, coping with malformed pages as well as possible.",
      long_description = long_description,
      classifiers = [
          'Development Status :: 3 - Alpha',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: GNU General Public License (GPL)',
          'Programming Language :: C++',
          'Topic :: Internet :: WWW/HTTP :: Indexing/Search',
          'Operating System :: MacOS',
          'Operating System :: Microsoft',
          'Operating System :: POSIX',
      ],
      license = 'GPL',
      platforms = 'Any',

      ext_modules = [Extension("htmltotext",
                               htmltotext_sources,
                               include_dirs=['src'] + extra_include_dirs,
                               library_dirs=extra_library_dirs,
                               libraries=['libiconv']
                              )],
                              
      **extra_kwargs)
