#! /usr/bin/env python

###
# Caveat:
# If input is read from stdin, it should be of one type
# (text/plain, text/html, email) because the type detecting
# mechanism is only triggered once.
# However you should be able to run this on all kind of files,
# input is checked anew for each file.
###

import getopt, os, re, sys
from Urlregex import Urlregex, mailCheck, ftpCheck
from LastExit import LastExit
try: from conny import pppConnect
except ImportError: pass
from kiosk import Kiosk
from datatype import dataType
from spl import sPl
from getbin import getBin
from selbrowser import finderCheck

optstring = "d:ghik:lnr:"
mackies = ('launch', 'open')

def Usage(msg=''):
	scriptname = os.path.basename(sys.argv[0])
	if msg: print msg
	print 'Usage:\n' \
	'%(sn)s [-r <pattern>][file ...]\n' \
	'%(sn)s -i [-l][-r <pattern>][-d <mail hierarchy>[:<mail hierarchy> ...]][-k <mbox>][<file> ...]\n' \
	'%(sn)s -i -n [-l][-r <pattern>][-k <mbox>][<file> ...]\n' \
	'%(sn)s -i -g [-r <pattern>][-k <mbox>][<file> ...]\n' \
	'%(sn)s -h' \
	% { 'sn':scriptname }
	sys.exit(2)

def parseError():
	errmsg = '*Encountered malformed html!*\n' \
		 'Might be unable to retrieve every url.\n' \
		 'Continue? ([RET], No) '
	if raw_input(errmsg) in ('n', 'N'):
		sys.exit()

class Urlbatcher(Urlregex, Kiosk, LastExit):
	"""
	Parses input for either web urls or message-ids.
	Browses all urls or creates a message tree in mutt.
	You can specify urls/ids by a regex pattern.
	"""
	def __init__(self):
		Urlregex.__init__(self, 'web') # <- proto, id, items
		Kiosk.__init__(self) # <- nt, kiosk, mdirs, local, google
		LastExit.__init__(self)
		self.files = []    # files to search
		self.pat = None

	def argParser(self):
		try: opts, self.files = getopt.getopt(sys.argv[1:], optstring)
		except getopt.GetoptError, msg: Usage(msg)
		for o, a in opts:
			if o == '-d': # specific mail hierarchies
				self.id = 1
				self.proto = 'all'
				self.mdirs = a.split(':')
			elif o == '-h': Usage()
			elif o == '-g': # go to google directly for message-ids
				self.proto = 'all'
				self.id, self.google, self.mdirs = 1, 1, []
			elif o == '-i': # look for message-ids
				self.proto = 'all'
				self.id = 1
			elif o == '-k': # mailbox to store retrieved messages
				self.proto = 'all'
				self.id, self.kiosk = 1, a
			elif o == '-l': # only local search for message-ids
				self.id, self.local = 1, 1
			elif o == '-n': # don't search local mailboxes
				self.proto = 'all'
				self.id, self.mdirs = 1, []
			elif o == '-r':
				self.pat = a

	def urlGo(self):
		conny = 0
		for url in self.items:
			if not url.startswith('file://'):
				conny = 1
				break
		self.items = [self.httpAdd(url) for url in self.items]
		bin = getBin(mackies)
		if conny:
			try: pppConnect()
			except NameError: pass
		if bin == 'launch':
			cmd = "%s '%s'" % (bin, "', '".join(self.items))
			os.system(cmd)
		else:
			for url in self.items:
				cmd = "%s '%s'" % (bin, url)
				os.system(cmd)
					
	def urlSearch(self):
		if not self.id and not finderCheck():
			Usage('only works on Macs')
		if not self.files: # read from stdin
			data = sys.stdin.read()
			Urlregex.findUrls(self, data)
			LastExit.termInit(self)
		else:
			for f in self.files:
				data, type = dataType(f)
				Urlregex.findUrls(self, data, type)
		if self.ugly: parseError()
		if self.pat and self.items:
			try: self.pat = re.compile(r'%s' % self.pat, re.IGNORECASE)
			except re.error, strerror: Usage(strerror)
			self.items = filter(lambda i: self.pat.search(i), self.items)
		try:
			ilen = len(self.items)
			if ilen and not self.id:
				yorn = 'Really visit %s? [y,N] ' \
				       % sPl(ilen, 'url')
				if raw_input(yorn) in ('y', 'Y'):
					self.urlGo()
			elif ilen:
				yorn = 'Collect %s? [y/N] ' \
				       % sPl(ilen, 'message')
				if raw_input(yorn) in ('y', 'Y'):
					if not self.files: self.nt = 1
					Kiosk.kioskStore(self)
			else:
				msg = 'No %s found. [Enter] ' \
				      % ('urls', 'message-ids')[self.id]
				raw_input(msg)
		except KeyboardInterrupt: pass
		if not self.files: LastExit.reInit(self)



def main():
	up = Urlbatcher()
	up.argParser()
	up.urlSearch()

if __name__ == '__main__':
	main()
