# $Hg: datatype.py,v$

import urllib2
from cheutils import filecheck

def dataType(path):
    path = filecheck.fileCheck(path, spec='isfile', absolute=True)
    try:
        fp = urllib2.urlopen('file://%s' % path)
        kind = fp.info().gettype()
        data = fp.read()
    finally:
        fp.close()
    return data, kind
