# $Hg: Urlcollector.py,v$

import re, sys
from tpager.LastExit import LastExit
from Urlregex import Urlregex

class UrlcollectorError(Exception):
	'''Exception class for this module.'''

class Urlcollector(Urlregex, LastExit):
	'''
	Provides function to retrieve urls
	from files or input stream.
	'''
	def __init__(self, proto='all'):
		Urlregex.__init__(self, proto=proto) # <- proto, decl, items
		LastExit.__init__(self)
		self.files = []         # files to search
		self.pat = None         # pattern to match urls against

	def urlCollect(self):
		if not self.files: # read from stdin
			try:
				data = sys.stdin.read()
			except KeyboardInterrupt:
				print
				raise UrlcollectorError, \
					'needs stdin or filename(s)'
			Urlregex.findUrls(self, data)
		else:
			import datatype
			for f in self.files:
				data, kind = datatype.dataType(f)
				Urlregex.findUrls(self, data, kind)
		if self.pat and self.items:
			try:
				self.pat = re.compile(r'%s' % self.pat, re.I)
			except re.error, e:
				raise UrlcollectorError, \
					"%s in pattern `%s'" % (e, self.pat)
			self.items = filter(lambda i: self.pat.search(i),
					self.items)
