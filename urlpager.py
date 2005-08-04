#! /usr/bin/env python
# $Id: urlpager.py,v 1.11 2005/08/04 21:09:50 chris Exp $

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
from selbrowser import selBrowser, local_re

optstring = "bd:D:f:ghiIlnp:k:r:tw:x"
mailers = ('mutt', 'pine', 'elm', 'mail')

def Usage(msg=''):
	scriptname = os.path.basename(sys.argv[0])
	if msg: print msg
	print 'Usage:\n' \
	'%(sn)s [-p <protocol>][-r <pattern>][-t][-x][-f <ftp client>][<file> ...]\n' \
	'%(sn)s -w <download dir> [-r <pattern]\n' \
	'%(sn)s -i [-r <pattern>][-k <mbox>][<file> ...]\n' \
	'%(sn)s -I [-r <pattern>][-k <mbox>][<file> ...]\n' \
	'%(sn)s -l [-I][-r <pattern>][-k <mbox>][<file> ...]\n' \
	'%(sn)s -d <mail hierarchy>[:<mail hierarchy>[:...]] [-I][-l][-r <pattern>][-k <mbox>][<file> ...]\n' \
	'%(sn)s -D <mail hierarchy>[:<mail hierarchy>[:...]] [-I][-l][-r <pattern>][-k <mbox>][<file> ...]\n' \
	'%(sn)s -n [-r <pattern][-I][-l][-k <mbox>][<file> ...]\n' \
	'%(sn)s -g [-r <pattern][-I][-k <mbox>][<file> ...]\n' \
	'%(sn)s -b [-r <pattern][-I][<file> ...]\n' \
	'%(sn)s -h' \
	% { 'sn':scriptname }
	sys.exit(2)


class Urlpager(Urlcollector, Kiosk, Tpager, LastExit):
	def __init__(self):
		Urlcollector.__init__(self) # <- proto, id, laxid, items, files, pat
		Kiosk.__init__(self) # <- browse, google, nt, kiosk, mdirs, local
		Tpager.__init__(self, name='url') # <- items, name
		LastExit.__init__(self)
		self.ft = ''	   # ftpclient
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
			elif o == '-f': # ftp client
				getBin([a])
				self.ft = a
			elif o == '-g': # don't look up msgs locally
				self.id, self.google, self.mdirs = 1, 1, []
			elif o == '-h': Usage()
			elif o == '-I': # look for declared message-ids
				self.id, self.decl = 1, 1
				self.getdir = ''
			elif o == '-i': # look for ids, in text w/o prot (email false positives)
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
			elif o == '-w': # download dir for wget
				getBin(['wget'])
				self.proto = 'web'
				self.getdir = a
				self.getdir = os.path.abspath(os.path.expanduser(self.getdir))
				if not os.path.isdir(self.getdir):
					Usage('%s: not a directory' % self.getdir)
				self.id = 0

	def urlPager(self):
		if not self.id and self.proto != 'all':
			self.name = '%s %s' % (self.proto, self.name)
		elif self.id: self.name = 'message-id'
		self.name = 'unique %s' % self.name
		self.url = Tpager.interAct(self)

	def urlGo(self):
		bin = ''
		conny = local_re.search(self.url) == None
		if self.proto == 'mailto' \
		or self.proto == 'all' and mailCheck(self.url):
			bin = getBin(mailers)
			conny = False
		elif self.getdir:
			if not conny:
				Usage("wget doesn't retrieve local files")
			bin = "wget -P '%s'" % self.getdir
		elif self.proto == 'ftp' or self.ft or ftpCheck(self.url):
			if not self.ft: bin = 'ftp'
			else: bin = self.ft
			self.nt = 1
		if not bin: selBrowser([self.url], self.tb, self.xb)
		else:
			if not self.files and not self.getdir or self.nt: # program needs terminal
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
