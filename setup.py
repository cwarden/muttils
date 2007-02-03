#!/usr/bin/env python
# $Id$

from distutils.core import setup
import urlregex.version

# specify version, Mercurial version otherwise
version = ''

urlregex.version.rememberversion(version)

setup(name='urlregex',
        version=urlregex.version.getversion(),
        description='Python utilities to detect and retrieve urls',
        author='Christian Ebert',
        author_email='blacktrash@gmx.net',
        packages=['urlregex'],
        scripts=['kiosk', 'urlbatcher', 'urlpager'],
        )
