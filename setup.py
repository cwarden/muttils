#!/usr/bin/env python
# $Id$

from distutils.core import setup
import tpager.version

# specify version, Mercurial version otherwise
version = ''

tpager.version.rememberversion(version)

setup(name='tpager',
        version=tpager.version.getversion(),
        description='Python interactive terminal pager',
        author='Christian Ebert',
        author_email='blacktrash@gmx.net',
        packages=['tpager'],
        scripts=['sigpager'],
        )
