# $Hg: datatype.py,v$

import os.path, urllib
from cheutils import filecheck

def dataType(f):
	path = os.path.abspath(os.path.expanduser(f))
	filecheck.fileCheck(path)
	# urllib uses the deprecated mimelib
	# but email does not work for type detection
	# on local files
	# [ use urllib2? but then will have do revamp kiosk.py ]
	try:
		fp = urllib.urlopen('file://%s' % path)
		type = fp.info().gettype()
		data = fp.read()
	finally:
		fp.close()
	return data, type
