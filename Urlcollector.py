#!/usr/bin/env python

Urlcollector_rcsid = '$Id: Urlcollector.py,v 1.5 2005/12/17 11:51:32 chris Exp $'

import os, re, sys
from tpager.LastExit import LastExit
from cheutils.Rcsparser import Rcsparser
from Urlregex import Urlregex
from datatype import dataType

rcs = Rcsparser(Urlcollector_rcsid)

def inputError():
	print
	print rcs.getVals(shortv=True)
	print 'needs file arguments or standard input'
	sys.exit(2)

class Urlcollector(Urlregex, LastExit):
	"""
	Provides function to retrieve urls
	from files or input stream.
	"""
	def __init__(self, proto='all', nt=False):
		Urlregex.__init__(self, proto) # <- proto, id, decl, items
		LastExit.__init__(self)
		self.files =[]          # files to search
		self.pat = None         # pattern to match urls against
		self.nt = False         # needs terminal

	def parseError(self):
		print rcs.getVals(shortv=True)
		errmsg = 'Encountered malformed html!\n' \
			 'Might be unable to retrieve every url.\n' \
			 'Continue? [Yes], no '
		if self.nt: LastExit.termInit(self)
		yorn = raw_input(errmsg)
		if self.nt: LastExit.reInit(self)
		if yorn: sys.exit()

	def urlCollect(self):
		if not self.files: # read from stdin
			try: data = sys.stdin.read()
			except KeyboardInterrupt: inputError()
			Urlregex.findUrls(self, data)
		else:
			for f in self.files:
				data, type = dataType(f)
				Urlregex.findUrls(self, data, type)
		if self.ugly: self.parseError()
		if self.pat and self.items:
			try: self.pat = re.compile(r'%s' % self.pat, re.IGNORECASE)
			except re.error, strerror: Usage(strerror)
			self.items = filter(lambda i: self.pat.search(i), self.items)


def _test():
	sourcefile = sys.argv[0]
	print rcs.getVals(shortv=True)
	print """
hello world, these are 3 urls:
cis.tarzisius.net
www.python.org.
<www.black
trash.org>
they are contained in the source file %s
you are currently testing.
I will read myself now so to speak and
collect the urls:
	""" % sourcefile
	ur = Urlcollector()
	ur.files = [sourcefile]
	ur.urlCollect()
	print ur.items
#        os.unlink(tf)
	
if __name__ == '__main__': _test()

# EOF vim:ft=python
