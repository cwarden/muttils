#! /usr/bin/env python
# $Id: datatype.py,v 1.2 2005/02/04 16:30:24 chris Exp $

import os.path
import urllib

def Usage(path):
	import sys
	sn = os.path.basename(sys.argv[0])
	print '%s: %s: not a regular file.' % (sn, path)
	sys.exit(2)

def dataType(f):
	path = os.path.abspath(os.path.expanduser(f))
	if not os.path.isfile(path): Usage(path)
	# urllib uses the deprecated mimelib
	# but email does not work for type detection
	# on local files
	fp = urllib.urlopen('file://%s' % path)
	type = fp.info().gettype()
	data = fp.read()
	fp.close()
	return data, type
