# $Hg$

import re
from tpager.LastExit import LastExit
from Urlregex import Urlregex
from cheutils import exnam

def collectErr(err):
	import sys
	sys.exit("%s: %s" % (exnam.exNam(), err))


class Urlcollector(Urlregex, LastExit):
	"""
	Provides function to retrieve urls
	from files or input stream.
	"""
	def __init__(self, proto="all", nt=False):
		Urlregex.__init__(self, proto) # <- proto, id, decl, items
		LastExit.__init__(self)
		self.files =[]          # files to search
		self.pat = None         # pattern to match urls against
		self.nt = False         # needs terminal

	def parseError(self):
		errmsg = "%s: encountered malformed html!\n" \
			 "Might be unable to retrieve every url.\n" \
			 "Continue? [Yes], no " % exnam.exNam()
		if self.nt:
			LastExit.termInit(self)
		yorn = raw_input(errmsg)
		if self.nt:
			LastExit.reInit(self)
		if yorn in ("n", "N"):
			sys.exit()

	def urlCollect(self):
		if not self.files: # read from stdin
			import sys
			try:
				data = sys.stdin.read()
			except KeyboardInterrupt:
				print
				collectErr("needs stdin or filename(s)")
			Urlregex.findUrls(self, data)
		else:
			import datatype
			for f in self.files:
				data, type = datatype.dataType(f)
				Urlregex.findUrls(self, data, type)
		if self.ugly:
			self.parseError()
		if self.pat and self.items:
			try:
				self.pat = re.compile(r"%s" % self.pat, re.I)
			except re.error, e:
				collectErr("%s in pattern `%s'" % (e, self.pat))
			self.items = filter(lambda i: self.pat.search(i),
					self.items)
