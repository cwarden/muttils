# $Id: Urlcollector.py,v 1.1 2005/02/04 16:29:23 chris Exp $
import os, re, sys
from datatype import dataType
from Urlregex import Urlregex

def parseError():
	scriptname = os.path.basename(sys.argv[0])
	errmsg = '%s: Encountered malformed html!\n' \
		 'Might be unable to retrieve every url.\n' \
		 'Continue? ([RET], No) ' % scriptname
	if raw_input(errmsg) in ('n', 'N'):
		sys.exit()


class Urlcollector(Urlregex):
	"""
	Provides function to retrieve urls
	from files or input stream.
	"""
	def __init__(self):
		Urlregex.__init__(self) # <- proto, id, items
		self.files =[]          # files to search
		self.pat = None         # pattern to match urls against

	def urlCollect(self):
		if not self.files: # read from stdin
			data = sys.stdin.read()
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
