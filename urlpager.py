#! /usr/bin/env python

###
# Caveat:
# If input is read from stdin, it should be of one type
# (text/plain, text/html, email) because the type detecting
# mechanism is only triggered once.
# However you should be able to run this on all kind of files,
# input is checked anew for each file.
###

import getopt, os, readline, sys
from Urlregex import Urlregex, mailCheck, ftpCheck
from LastExit import LastExit
from Tpager import Tpager
try: from conny import pppConnect
except ImportError: pass
from datatype import dataType
from kiosk import Kiosk
from getbin import getBin
from selbrowser import selBrowser

optstring = "bd:D:f:ghilnp:k:tw:x"
mailers = ('mutt', 'pine', 'elm', 'mail')
ftpclients = ('ftp', 'lftp', 'ncftp', 'ncftpget')

def Usage(msg=''):
	scriptname = os.path.basename(sys.argv[0])
	if msg: print msg
	print 'Usage:\n' \
	'%(sn)s [-p <protocol>][-t][-x][-f <ftp client>][<file> ...]\n' \
	'%(sn)s -w <download dir>\n' \
	'%(sn)s -i [<file> ...]\n' \
	'%(sn)s [-i][-l][-k <mbox>][-d <mail hierarchy>[:<mail hierarchy> ...]][<file> ...]\n' \
	'%(sn)s [-i][-l][-k <mbox>][-D <mail hierarchy>[:<mail hierarchy> ...]][<file> ...]\n' \
	'%(sn)s [-i][-l][-k <mbox>] -n [<file> ...]\n' \
	'%(sn)s [-i][-k <mbox>] -g [<file> ...]\n' \
	'%(sn)s [-i][-g] -b [<file> ...]\n' \
	'%(sn)s -h' \
	% { 'sn':scriptname }
	sys.exit(2)

def parseError():
	errmsg = '*Encountered malformed html!*\n' \
		 'Might be unable to retrieve every url.\n' \
		 'Continue? ([RET], No) '
	if raw_input(errmsg) in ('n', 'N'):
		sys.exit()

class Urlpager(Urlregex, Kiosk, Tpager, LastExit):
	def __init__(self):
		Urlregex.__init__(self) # <- proto, id, items
		Kiosk.__init__(self) # <- browse, google, nt, kiosk, mdirs, local
		Tpager.__init__(self, name='url') # <- items, name
		LastExit.__init__(self)
		self.files = []    # files to search
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
			elif o == '-d': # add specific mail hierarchies
				self.id = 1
				self.mdirs = self.mdirs + a.split(':')
			elif o == '-D': # specific mail hierarchies
				self.id = 1
				self.mdirs = a.split(':')
			elif o == '-g': # don't look up msgs locally
				self.id, self.google, self.mdirs = 1, 1, []
			elif o == '-h': Usage()
			elif o == '-i': # look for message-ids
				self.id = 1
			elif o == '-k': # mailbox to store retrieved message
				self.id = 1
				self.kiosk = a
			elif o == '-l': # only local search for message-ids
				self.local, self.id = 1, 1
			elif o == '-n': # don't search mailboxes for message-ids
				self.id, self.mdirs = 1, []
			elif o == '-p': # protocol(s)
				self.id = 0
				self.proto = a
			elif o == '-x': # xbrowser
				self.id, self.xb = 0, 1
			elif o == '-t': # text browser command
				self.id, self.tb = 0, 1
			elif o == '-f': # ftp client
				self.id = 0
				self.ft = a
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
		elif self.proto == 'ftp' \
		or self.ft and not self.id and not mailCheck(self.url) \
		or self.proto in ('all', 'web') and ftpCheck(self.url):
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
		if not self.files: # read from stdin
			data = sys.stdin.read()
			Urlregex.findUrls(self, data)
			LastExit.termInit(self)
		else:
			for f in self.files:
				data, type = dataType(f)
				Urlregex.findUrls(self, data, type)
		if self.ugly: parseError()
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
