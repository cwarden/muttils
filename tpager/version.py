# $Id$

import os, time

unknown_version = 'unknown'

def getversion():
    try:
        from tpager.__version__ import version
    except ImportError:
        version = unknown_version
    return version

def writeversion(version):
    if version == getversion():
        return
    directory = os.path.dirname(__file__)
    for suff in ['py', 'pyc', 'pyo']:
        try:
            os.unlink(os.path.join(directory, '__version__.%s' % suff))
        except OSError:
            pass
    fp = open(os.path.join(directory, '__version__.py'), 'w')
    fp.write('# this file is auto-generated\n')
    fp.write('version = %r\n' % version)
    fp.close()

def rememberversion(version=None):
    if not version and os.path.isdir('.hg'):
        p = os.popen('hg --quiet identify 2> /dev/null') # in Mercurial directory
        ident = p.read()[:-1]
        if not p.close() and ident:
            if ident[-1] != '+':
                version = ident
            else:
                version = ident[:-1]
                version += time.strftime('+%Y%m%d')
    if version:
        writeversion(version)
