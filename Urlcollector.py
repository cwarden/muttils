# $Hg: Urlcollector.py,v$

import re
from tpager.LastExit import LastExit
from Urlregex import Urlregex

def collectErr(err):
	from sys import exit
	from cheutils.exnam import exNam
	exit("%s: %s" % (exNam(), err))


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
		from cheutils.exnam import exNam
		errmsg = "%s: encountered malformed html!\n" \
			 "Might be unable to retrieve every url.\n" \
			 "Continue? [Yes], no " % exNam()
		if self.nt:
			LastExit.termInit(self)
		yorn = raw_input(errmsg)
		if self.nt:
			LastExit.reInit(self)
		if yorn in ("n", "N"):
			sys.exit()

	def urlCollect(self):
		if not self.files: # read from stdin
			from sys import stdin
			try:
				data = stdin.read()
			except KeyboardInterrupt:
				collectErr("needs stdin or filename(s)")
			Urlregex.findUrls(self, data)
		else:
			from datatype import dataType
			for f in self.files:
				data, type = dataType(f)
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
