#!/usr/bin/env python

Urlcollector_rcsid = '$Id: Urlcollector.py,v 1.3 2005/08/22 19:36:34 chris Exp $'

import os, re, sys
from datatype import dataType
from Rcsparser import Rcsparser
from Urlregex import Urlregex

rcs = Rcsparser(Urlcollector_rcsid)

def parseError():
	print rcs.getVals(shortv=True)
	errmsg = 'Encountered malformed html!\n' \
		 'Might be unable to retrieve every url.\n' \
		 'Continue? ([RET], No) '
	if raw_input(errmsg) in ('n', 'N'): sys.exit()

def inputError():
	print
	print rcs.getVals(shortv=True)
	print 'needs file arguments or standard input'
	sys.exit(2)

class Urlcollector(Urlregex):
	"""
	Provides function to retrieve urls
	from files or input stream.
	"""
	def __init__(self, proto='all'):
		Urlregex.__init__(self, proto) # <- proto, id, decl, items
		self.files =[]          # files to search
		self.pat = None         # pattern to match urls against

	def urlCollect(self):
		if not self.files: # read from stdin
			try: data = sys.stdin.read()
			except KeyboardInterrupt: inputError()
			Urlregex.findUrls(self, data)
		else:
			for f in self.files:
				data, type = dataType(f)
				Urlregex.findUrls(self, data, type)
		if self.ugly: parseError()
		if self.pat and self.items:
			try: self.pat = re.compile(r'%s' % self.pat, re.IGNORECASE)
			except re.error, strerror: Usage(strerror)
			self.items = filter(lambda i: self.pat.search(i), self.items)


def _test():
	print rcs.getVals(shortv=True)
	print """
hello world, these are 3 urls:
cis.tarzisius.net
www.python.org.
<www.black
trash.org>
please read yourself and collect them!
"""
	ur = Urlcollector()
	ur.files = [rcs.rcsdict['rcsfile']]
	ur.urlCollect()
	print ur.items
	
if __name__ == '__main__': _test()

# EOF vim:ft=python
