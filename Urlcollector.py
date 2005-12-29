# $Id: Urlcollector.py,v 1.6 2005/12/29 17:50:10 chris Exp $

import os.path, re, sys
from tpager.LastExit import LastExit
from Urlregex import Urlregex
from datatype import dataType

def exNam(): return os.path.basename(sys.argv[0])

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
		errmsg = '%s: encountered malformed html!\n' \
			 'Might be unable to retrieve every url.\n' \
			 'Continue? [Yes], no ' % exNam()
		if self.nt: LastExit.termInit(self)
		yorn = raw_input(errmsg)
		if self.nt: LastExit.reInit(self)
		if yorn in ('n', 'N'): sys.exit()

	def urlCollect(self):
		if not self.files: # read from stdin
			try: data = sys.stdin.read()
			except KeyboardInterrupt:
				err = '\n%s: needs stdin or filename(s)' \
						% exNam()
				sys.exit(err)
			Urlregex.findUrls(self, data)
		else:
			for f in self.files:
				data, type = dataType(f)
				Urlregex.findUrls(self, data, type)
		if self.ugly: self.parseError()
		if self.pat and self.items:
			try: self.pat = re.compile(r'%s' % self.pat, re.I)
			except re.error, e:
				err = '%s: %s in pattern %s' \
						% (exNam(), e, self.pat)
				sys.exit(err)
			self.items = filter(lambda i: self.pat.search(i),
					self.items)
