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
r"""install_dependencies.py: Install all the dependencies for flax.

This installs the dependencies in a local installation directory, which flax
adds to its search path at startup, so root privileges are not needed.

"""
__docformat__ = "restructuredtext en"

import glob
import os
import sha
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib2

# List of the python packages which are dependencies.
# FIXME - xappy should be in this list (but doesn't yet have package scripts
# written).
#
# The values are, in order:
#  - Descriptive name of dependency
#  - URL to download
#  - Filename to store downloaded package as
#  - SHA1 sum of package
#  - Directories that needs to be moved to install dir after running setup.py
#    (relative to install dir)  (with unix-style slashes, and globs)
python_dependencies = (
    ('HTMLTemplate templating system',
     'http://flaxcode.googlecode.com/files/HTMLTemplate-1.4.2.tar.gz',
     'HTMLTemplate.tar.gz',
     '051a278402aeeb913c75dc3dc2eef57080332167',
     (),
    ),
    ('CherryPy web application server',
     'http://flaxcode.googlecode.com/files/CherryPy-3.0.2.tar.gz',
     'CherryPy.tar.gz',
     '8aae47ff892b42761c21ca552222f8f251dbc1b2',
     (),
    ),
    ('HtmlToText text extractor',
     'libs://htmltotext',
     '',
     '',
     (),
    ),
    ('Xappy search engine interface',
     'libs://xappy',
     '',
     '',
     (),
    ),
)

# List of the non-pure-python dependencies.
# FIXME - none yet, but Xapian should be one.

def get_script_dir():
    """Get the path of the directory containing this script.

    """
    global scriptdir
    if 'scriptdir' not in globals():
        scriptdir = os.path.dirname(os.path.abspath(__file__))
    return scriptdir

def get_package_dir():
    """Get the path to store the downloaded packages in.
    
    This is a standard location relative to this script.

    """
    return os.path.abspath(os.path.join(get_script_dir(), '..', 'deps'))

def get_install_dir():
    """Get the path to install the dependencies in.
     
    This is a standard location relative to this script.

    """
    return os.path.abspath(os.path.join(get_script_dir(), '..', 'localinst'))

def calc_sha_hash(filepath):
    """Calculate the SHA1 hash of the file at the given path.

    """
    hasher = sha.new()
    fd = open(filepath, 'rb', 0)
    try:
        while True:
            chunk = fd.read(65536)
            if len(chunk) == 0:
                break
            hasher.update(chunk)
    finally:
        fd.close()
    return hasher.hexdigest()

def download_file(url, destpath):
    """Download a file, and place it in destpath.

    """
    destdir = os.path.dirname(destpath)
    if not os.path.isdir(destdir):
        os.makedirs(destdir)

    fd = urllib2.urlopen(url)
    tmpfd, tmpname = tempfile.mkstemp(dir=destdir, prefix='flax')
    try:
        os.write(tmpfd, fd.read())
        os.close(tmpfd)
        os.rename(tmpname, destpath)
    finally:
        if os.path.exists(tmpname):
            os.unlink(tmpname)

def unpack_archive(filename, tempdir):
    """Unpack the archive at filename.
    
    Puts the contents in a directory with basename tempdir.

    """
    tf = tarfile.open(filename)
    try:
        dirname = None
        for member in tf.getmembers():
            topdir = member.name.split('/', 1)[0]
            if dirname is None:
                dirname = topdir
            else:
                if dirname != topdir:
                    raise ValueError('Archive has multiple toplevel directories: %s and %s' % (topdir, dirname))
            tf.extract(member, path=tempdir)
        return os.path.join(tempdir, dirname)
    finally:
        tf.close()

def install_archive(archivedir, install_dir):
    """Install the unpacked archive in install_dir.

    """
    setupcmd = [sys.executable]
    setupcmd.append(os.path.join(archivedir, 'setup.py'))
    setupcmd.append('install')
    setupcmd.append('--install-lib=%s' % install_dir)
    setupcmd.append('--install-headers=%s' % install_dir)
    setupcmd.append('--install-scripts=%s' % install_dir)
    setupcmd.append('--install-data=%s' % install_dir)
    env = {'PYTHONPATH': ':'.join(sys.path + [install_dir])}
    os.chdir(archivedir)
    subp = subprocess.Popen(setupcmd, env=env,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    subout, suberr = subp.communicate()
    rc = subp.wait()
    if rc != 0:
        if subout:
            print subout
        if suberr:
            print "ERRORS:"
            print suberr
        print("Failed")
        return False
    if suberr:
        print suberr

    return True

def get_archive_from_url(name, url, archivename, expected_hash):
    """Download and unpack an archive from the specified URL.

    Returns the directory the archive was unpacked into, or None if
    the archive couldn't be downloaded

    """
    if url.startswith('libs://'):
        libsdir = os.path.join(get_script_dir(), '..', 'libs')
        archivedir = os.path.join(libsdir, url[7:])
    else:
        print("Checking for %s" % name)

        # Get the path that the package should be downloaded to
        filepath = os.path.join(package_dir, archivename)

        # Check if the package is already downloaded (and has correct SHA key).
        if os.path.exists(filepath):
            calculated_hash = calc_sha_hash(filepath)
            if expected_hash != calculated_hash:
                print("Package of %s at '%s' has wrong hash - discarding" % (name, archivename))
                print("(Got %s, expected %s)" % (calculated_hash, expected_hash))
                os.unlink(filepath)

        # Download the package if needed.
        if not os.path.exists(filepath):
            print("Downloading %s from %s" % (name, url))
            download_file(url, filepath)
            calculated_hash = calc_sha_hash(filepath)
            if expected_hash != calculated_hash:
                print("Package of %s at '%s' has wrong hash - cannot continue" % (name, archivename))
                print("(Got %s, expected %s)" % (calculated_hash, expected_hash))
                os.unlink(filepath)
                return None

        print("Unpacking %s" % name)
        archivedir = unpack_archive(filepath, temp_dir)

    return archivedir

def install_pure_deps(dependencies, temp_dir):
    """Download and install the pure python dependencies.

    """
    package_dir = get_package_dir()
    install_dir = get_install_dir()
    for name, url, archivename, expected_hash, movedirs in dependencies:
        archivedir = get_archive_from_url(name, url, archivename, expected_hash)
        if archivedir is None:
            return False

        print("Installing %s" % name)
        if not install_archive(archivedir, install_dir):
            return False

        for movedir in movedirs:
            movedir = movedir.replace('/', os.path.sep)
            movedir = os.path.join(install_dir, movedir)
            for movedir in glob.glob(movedir):
                destdir = os.path.join(install_dir, os.path.basename(movedir))
                if os.path.exists(destdir):
                    shutil.rmtree(destdir)
                os.rename(movedir, destdir)

        print("")
    return True
        
if __name__ == '__main__':
    package_dir = get_package_dir()
    install_dir = get_install_dir()
    temp_dir = tempfile.mkdtemp(prefix='flax')
    try:
        if not install_pure_deps(python_dependencies, temp_dir):
            sys.exit(1)

        sys.exit(0)
    finally:
        shutil.rmtree(temp_dir)

