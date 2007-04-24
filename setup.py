#!/usr/bin/env python
# $Id$

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
