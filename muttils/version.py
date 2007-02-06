# $Id$

'''version.py - muttils version.
Code stolen from Mercurial, and simplified for my needs.
'''

import os, time

unknown_version = 'unknown'

def getversion(doreload=False):
    try:
        import muttils.__version__
        if doreload:
            reload(muttils.__version__)
        version = muttils.__version__.version
    except ImportError:
        version = unknown_version
    return version

def rememberversion(version=None):
    if not version and os.path.isdir('.hg'):
        # get version from Mercurial
        p = os.popen('hg --quiet identify 2> %s' % os.devnull)
        ident = p.read()[:-1]
        if not p.close() and ident:
            if ident[-1] != '+':
                version = ident
            else:
                version = ident[:-1]
                version += time.strftime('+%Y%m%d')
    if version and version != getversion(): # write version
        directory = os.path.dirname(__file__)
        for suff in ['py', 'pyc', 'pyo']:
            try:
                os.unlink(os.path.join(directory, '__version__.%s' % suff))
            except OSError:
                pass
        f = open(os.path.join(directory, '__version__.py'), 'w')
        try:
            f.write('# this file is auto-generated\n')
            f.write('version = %r\n' % version)
        finally:
            f.close()
        # reload file
        getversion(doreload=True)
