#! /usr/bin/env python
# $Id: urlbatcher.py,v 1.4 2005/02/04 16:32:44 chris Exp $

###
# Caveat:
# If input is read from stdin, it should be of one type
# (text/plain, text/html, email) because the type detecting
# mechanism is only triggered once.
# However you should be able to run this on all kind of files,
# input is checked anew for each file.
###

import getopt, os, sys
from Urlcollector import Urlcollector
from LastExit import LastExit
from Urlregex import mailCheck, ftpCheck
try: from conny import pppConnect
except ImportError: pass
from kiosk import Kiosk
from spl import sPl
from selbrowser import selBrowser

optstring = "d:ghik:lnr:w:x"

def Usage(msg=''):
	scriptname = os.path.basename(sys.argv[0])
	if msg: print msg
	print 'Usage:\n' \
	'%(sn)s [-x][-r <pattern>][file ...]\n' \
	'%(sn)s -w <download dir> [-r <pattern]\n' \
	'%(sn)s -i [-l][-r <pattern>][-k <mbox>][<file> ...]\n' \
	'%(sn)s -d <mail hierarchy>[:<mail hierarchy>[:...]] [-l][-r <pattern>][-k <mbox>][<file> ...]\n' \
	'%(sn)s -D <mail hierarchy>[:<mail hierarchy>[:...]] [-l][-r <pattern>][-k <mbox>][<file> ...]\n' \
	'%(sn)s -n [-l][-r <pattern>][-k <mbox>][<file> ...]\n' \
	'%(sn)s -g [-r <pattern>][-k <mbox>][<file> ...]\n' \
	'%(sn)s -h' \
	% { 'sn':scriptname }
	sys.exit(2)


class Urlbatcher(Urlcollector, Kiosk, LastExit):
	"""
	Parses input for either web urls or message-ids.
	Browses all urls or creates a message tree in mutt.
	You can specify urls/ids by a regex pattern.
	"""
	def __init__(self):
		Urlcollector.__init__(self) # <- proto, id, items, files, pat
		Kiosk.__init__(self)        # <- nt, kiosk, mdirs, local, google
		LastExit.__init__(self)
		self.xb = 0                 # force x-browser
		self.getdir = ''            # download in dir via wget
		self.proto = 'web'

	def argParser(self):
		try: opts, self.files = getopt.getopt(sys.argv[1:], optstring)
		except getopt.GetoptError, msg: Usage(msg)
		for o, a in opts:
			if o == '-d': # specific mail hierarchies
				self.id = 1
				self.proto = 'all'
				self.mdirs = a.split(':')
				self.getdir = ''
			elif o == '-h': Usage()
			elif o == '-g': # go to google directly for message-ids
				self.proto = 'all'
				self.id, self.google, self.mdirs = 1, 1, []
				self.getdir = ''
			elif o == '-i': # look for message-ids
				self.proto = 'all'
				self.id = 1
				self.getdir = ''
			elif o == '-k': # mailbox to store retrieved messages
				self.proto = 'all'
				self.id, self.kiosk = 1, a
				self.getdir = ''
			elif o == '-l': # only local search for message-ids
				self.id, self.local = 1, 1
				self.getdir = ''
			elif o == '-n': # don't search local mailboxes
				self.proto = 'all'
				self.id, self.mdirs = 1, []
				self.getdir = ''
			elif o == '-r':
				self.pat = a
			elif o == '-w': # download dir for wget
				self.id = 0
				getdir = a
				self.getdir = os.path.abspath(os.path.expanduser(getdir))
				if not os.path.isdir(self.getdir):
					Usage('%s: not a directory' % self.getdir)
			elif o == '-x': # xbrowser
				self.xb, self.id, self.getdir = 1, 0, ''

	def urlGo(self):
		conny = 0
		bin = ''
		for url in self.items:
			if not url.startswith('file://'):
				try: pppConnect()
				except NameError: pass
				break
		if self.getdir:
			os.system("wget -P '%s'" % "' '".join(self.items))
		else:
			for url in self.items: selBrowser(url, 0, self.xb)
			# put above into selbrowser.py
			# doesn't work with firefox yet; try to solve in selbrowser.py
					
	def urlSearch(self):
		Urlcollector.urlCollect(self)
		if not self.files: LastExit.termInit(self)
		try:
			if self.items:
				yorn = '%s\nRetrieve the above %s? [y,N] ' \
				       % ('\n'.join(self.items),
					  sPl(len(self.items),
				          	('url', 'message-id')[self.id])
					 )
				if raw_input(yorn) in ('y', 'Y'):
					if not self.id: self.urlGo()
					else:
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
