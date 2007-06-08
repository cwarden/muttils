#!/usr/bin/env python
# $Id$

import sys
if not hasattr(sys, 'version_info') or sys.version_info < (2, 4):
    raise SystemExit, 'Muttils requires Python 2.4 or later'

from distutils.core import setup
import muttils.version

# specify version, Mercurial version otherwise
version = ''

muttils.version.rememberversion(version)

setup(name='muttils',
        version=muttils.version.getversion(),
        description='Python utilities for console mail clients (eg. mutt)',
        author='Christian Ebert',
        author_email='blacktrash@gmx.net',
        packages=['muttils'],
        scripts=['sigpager', 'urlbatcher', 'urlpager', 'pybrowser', 'wrap'],
        )
