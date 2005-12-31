# $Id: datatype.py,v 1.5 2005/12/31 14:29:58 chris Exp $

import os.path
import urllib
from cheutils.filecheck import fileCheck

def dataType(f):
	path = os.path.abspath(os.path.expanduser(f))
	fileCheck(path)
	# urllib uses the deprecated mimelib
	# but email does not work for type detection
	# on local files
	try:
		fp = urllib.urlopen('file://%s' % path)
		type = fp.info().gettype()
		data = fp.read()
	finally: fp.close()
	return data, type
