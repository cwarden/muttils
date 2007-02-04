#!/usr/bin/env python
# $Id$

from distutils.core import setup
import urlregex.version
import tpager.version

# specify version, Mercurial version otherwise
version = ''

urlregex.version.rememberversion(version)
tpager.version.rememberversion(version)

setup(name='muttilities',
        version=urlregex.version.getversion(),
        description='Python utilities for console mail clients (eg. mutt)',
        author='Christian Ebert',
        author_email='blacktrash@gmx.net',
        packages=['urlregex', 'tpager'],
        scripts=['kiosk', 'urlbatcher', 'urlpager', 'sigpager'],
        )

