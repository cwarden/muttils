# $Id: datatype.py,v 1.3 2005/12/29 17:51:37 chris Exp $

import os.path
import urllib

def fileErr(path):
	import sys
	exe = os.path.basename(sys.argv[0])
	sys.exit('%s: %s: not a regular file.' % (exe, path))

def dataType(f):
	path = os.path.abspath(os.path.expanduser(f))
	if not os.path.isfile(path): fileErr(path)
	# urllib uses the deprecated mimelib
	# but email does not work for type detection
	# on local files
	try:
		fp = urllib.urlopen('file://%s' % path)
		type = fp.info().gettype()
		data = fp.read()
	finally: fp.close()
	return data, type

# EOF vim:ft=python
