# $Hg: datatype.py,v$

import urllib2
from cheutils import filecheck

def dataType(path):
    path = filecheck.fileCheck(path, spec='isfile', absolute=True)
    fp = urllib2.urlopen('file://%s' % path)
    try:
        kind = fp.info().gettype()
        data = fp.read()
    finally:
        fp.close()
    return data, kind
