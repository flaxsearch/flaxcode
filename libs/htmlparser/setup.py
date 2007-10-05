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

import distutils
from distutils.core import setup, Extension

from distutils import sysconfig

# Customise compiler options.
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

setup(name = "htmltotext",
      version = "0.5",
      ext_modules = [Extension("htmltotext",
                               htmltotext_sources,
                               include_dirs=['src'],
                              )])
