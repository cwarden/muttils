#! /usr/bin/env python
# $Id: urlpager.py,v 1.4 2005/02/04 16:26:04 chris Exp $

###
# Caveat:
# If input is read from stdin, it should be of one type
# (text/plain, text/html, email) because the type detecting
# mechanism is only triggered once.
# However you should be able to run this on all kind of files,
# input is checked anew for each file.
###

import getopt, os, readline, sys
from Urlcollector import Urlcollector
from LastExit import LastExit
from Tpager import Tpager
from Urlregex import mailCheck, ftpCheck
try: from conny import pppConnect
except ImportError: pass
from kiosk import Kiosk
from getbin import getBin
from selbrowser import selBrowser

optstring = "bd:D:f:ghilnp:k:r:tw:x"
mailers = ('mutt', 'pine', 'elm', 'mail')
ftpclients = ('ftp', 'lftp', 'ncftp', 'ncftpget')

def Usage(msg=''):
	scriptname = os.path.basename(sys.argv[0])
	if msg: print msg
	print 'Usage:\n' \
	'%(sn)s [-p <protocol>][-r <pattern>][-t][-x][-f <ftp client>][<file> ...]\n' \
	'%(sn)s -w <download dir> [-r <pattern]\n' \
	'%(sn)s -i [-l][-r <pattern>][-k <mbox>][<file> ...]\n' \
	'%(sn)s -d <mail hierarchy>[:<mail hierarchy>[:...]] [-l][-r <pattern>][-k <mbox>][<file> ...]\n' \
	'%(sn)s -D <mail hierarchy>[:<mail hierarchy>[:...]] [-l][-r <pattern>][-k <mbox>][<file> ...]\n' \
	'%(sn)s -n [-r <pattern][-l][-k <mbox>][<file> ...]\n' \
	'%(sn)s -g [-r <pattern][-k <mbox>][<file> ...]\n' \
	'%(sn)s -b [-r <pattern][<file> ...]\n' \
	'%(sn)s -h' \
	% { 'sn':scriptname }
	sys.exit(2)


class Urlpager(Urlcollector, Kiosk, Tpager, LastExit):
	def __init__(self):
		Urlcollector.__init__(self) # <- proto, it, items, files, pat
		Kiosk.__init__(self) # <- browse, google, nt, kiosk, mdirs, local
		Tpager.__init__(self, name='url') # <- items, name
		LastExit.__init__(self)
		self.ft = ''	   # ftp client
		self.xb = 0	   # force x-browser
		self.tb = 0	   # use text browser
		self.url = ''	   # selected url
		self.getdir = ''   # download in dir via wget

	def argParser(self):
		try: opts, self.files = getopt.getopt(sys.argv[1:], optstring)
		except getopt.GetoptError, msg: Usage(msg)
		for o, a in opts:
			if o == '-b': # don't look up msgs locally
				self.browse, self.id, self.google, self.mdirs = 1, 1, 1, []
				self.getdir = ''
			elif o == '-d': # add specific mail hierarchies
				self.id = 1
				self.mdirs = self.mdirs + a.split(':')
				self.getdir = ''
			elif o == '-D': # specific mail hierarchies
				self.id = 1
				self.mdirs = a.split(':')
				self.getdir = ''
			elif o == '-g': # don't look up msgs locally
				self.id, self.google, self.mdirs = 1, 1, []
			elif o == '-h': Usage()
			elif o == '-i': # look for message-ids
				self.id = 1
				self.getdir = ''
			elif o == '-k': # mailbox to store retrieved message
				self.id = 1
				self.kiosk = a
				self.getdir = ''
			elif o == '-l': # only local search for message-ids
				self.local, self.id = 1, 1
				self.getdir = ''
			elif o == '-n': # don't search mailboxes for message-ids
				self.id, self.mdirs = 1, []
				self.getdir = ''
			elif o == '-p': # protocol(s)
				self.id = 0
				self.proto = a
			elif o == '-r': # regex pattern to match urls against
				self.pat = a
			elif o == '-x': # xbrowser
				self.id, self.xb = 0, 1
			elif o == '-t': # text browser command
				self.id, self.tb = 0, 1
			elif o == '-f': # ftp client
				self.id = 0
				self.ft = a
				self.getdir = ''
			elif o == '-w': # download dir for wget
				self.id = 0
				self.getdir = a
				self.getdir = os.path.abspath(os.path.expanduser(self.getdir))
				if not os.path.isdir(self.getdir):
					Usage('%s: not a directory' % self.getdir)
				self.proto = 'web'

	def urlPager(self):
		if not self.id and self.proto != 'all':
			self.name = '%s %s' % (self.proto, self.name)
		elif self.id: self.name = 'message-id'
		self.name = 'unique %s' % self.name
		self.url = Tpager.interAct(self)

	def urlGo(self):
		bin = ''
		conny = 1
		if self.proto == 'mailto' \
		or self.proto == 'all' and mailCheck(self.url):
			bin = getBin(mailers)
			conny = 0
		elif self.getdir:
			bin = "wget -P '%s'" % self.getdir
		elif self.proto == 'ftp' or self.ft or ftpCheck(self.url):
			if self.ft: ftpclients = (self.ft)
			bin = getBin(ftpclients)
		if not bin:
			selBrowser(self.url, self.tb, self.xb)
		else:
			if not self.files and not self.getdir: # program needs terminal
				cmd = "%s '%s' < %s" % (bin, self.url, os.ctermid())
			else: cmd = "%s '%s'" % (bin, self.url)
			if conny:
				try: pppConnect()
				except NameError: pass
			os.system(cmd)
					
	def urlSearch(self):
		Urlcollector.urlCollect(self)
		if not self.files: LastExit.termInit(self)
		try:
			self.urlPager()
			if self.url:
				if not self.id: self.urlGo()
				else:
					if not self.files:
						self.nt = 1
					self.items = [self.url]
					Kiosk.kioskStore(self)
		except KeyboardInterrupt: pass
		if not self.files: LastExit.reInit(self)


def main():
	up = Urlpager()
	up.argParser()
	up.urlSearch()

if __name__ == '__main__':
	main()
