#!/usr/bin/env python

urlbatcher_rcsid = '$Id: urlbatcher.py,v 1.15 2005/12/29 17:53:26 chris Exp $'

###
# Caveat:
# If input is read from stdin, it should be of one type
# (text/plain, text/html, email) because the type detecting
# mechanism is only triggered once.
# However you should be able to run this on all kind of files,
# input is checked anew for each file.
###

import getopt, os, sys
from cheutils.getbin import getBin
from cheutils.spl import sPl
from cheutils.selbrowser import selBrowser, local_re
from cheutils.systemcall import systemCall
from tpager.LastExit import LastExit
from Urlcollector import Urlcollector
from Urlregex import mailCheck, ftpCheck
from kiosk import Kiosk

optstring = "d:D:ghiIk:lnr:Tw:x"

connyAS = os.path.join(os.environ["HOME"], 'AS', 'conny.applescript')
if os.path.exists(connyAS): connyAS = False

def Usage(err=''):
	exe = os.path.basename(sys.argv[0])
	if err: print >>sys.stderr, '%s: %s' % (exe, err)
	else:
		from cheutils.Rcsparser import Rcsparser
		rcs = Rcsparser(urlbatcher_rcsid)
		print rcs.getVals(shortv=True)
	sys.exit("""Usage:
%(exe)s [-x][-r <pattern>][file ...]
%(exe)s -w <download dir> [-r <pattern]
%(exe)s -i [-r <pattern>][-k <mbox>][<file> ...]
%(exe)s -I [-r <pattern>][-k <mbox>][<file> ...]
%(exe)s -l [-I][-r <pattern>][-k <mbox>][<file> ...]
%(exe)s -d <mail hierarchy>[:<mail hierarchy>[:...]]' \\
            [-l][-I][-r <pattern>][-k <mbox>][<file> ...] 
%(exe)s -D <mail hierarchy>[:<mail hierarchy>[:...]] \\
            [-l][-I][-r <pattern>][-k <mbox>][<file> ...]
%(exe)s -n [-l][-I][-r <pattern>][-k <mbox>][<file> ...] 
%(exe)s -g [-I][-r <pattern>][-k <mbox>][<file> ...]
%(exe)s -h (display this help)"""
	% { 'exe': exe } )


class Urlbatcher(Urlcollector, Kiosk, LastExit):
	"""
	Parses input for either web urls or message-ids.
	Browses all urls or creates a message tree in mutt.
	You can specify urls/ids by a regex pattern.
	"""
	def __init__(self):
		Urlcollector.__init__(self, proto='web') # <- nt, proto, id, decl, items, files, pat
		Kiosk.__init__(self)        # <- nt, kiosk, mdirs, local, google, xb, tb
		LastExit.__init__(self)
		self.getdir = ''            # download in dir via wget

	def argParser(self):
		try: opts, self.files = getopt.getopt(sys.argv[1:], optstring)
		except getopt.GetoptError, msg: Usage(msg)
		for o, a in opts:
			if o == '-d': # add specific mail hierarchies
				self.id = 1
				self.mdirs = self.mdirs + a.split(':')
				self.getdir = ''
			elif o == '-D': # specific mail hierarchies
				self.id = 1
				self.mdirs = a.split(':')
				self.getdir = ''
			elif o == '-h': Usage()
			elif o == '-g': # go to google directly for message-ids
				self.id, self.google, self.mdirs = 1, 1, []
				self.getdir = ''
			elif o == '-i': # look for message-ids
				self.id = 1
				self.getdir = ''
			elif o == '-I': # look for declared message-ids
				self.id, self.decl = 1, 1
				self.getdir = ''
			elif o == '-k': # mailbox to store retrieved messages
				self.id, self.kiosk = 1, a
				self.getdir = ''
			elif o == '-l': # only local search for message-ids
				self.local, self.id = 1, 1
				self.getdir = ''
			elif o == '-n': # don't search local mailboxes
				self.id, self.mdirs = 1, []
				self.getdir = ''
			elif o == '-r':
				self.pat = a
			elif o == '-T': # force new terminal
				self.nt = True
			elif o == '-w': # download dir for wget
				self.id = 0
				getdir = a
				self.getdir = os.path.abspath(os.path.expanduser(getdir))
				if not os.path.isdir(self.getdir):
					Usage('%s: not a directory' % self.getdir)
			elif o == '-x': # xbrowser
				self.xb, self.id, self.getdir = 1, 0, ''
			if self.id: self.proto = 'all'

	def urlGo(self):
		if self.getdir:
			for url in self.items:
				if local_re.search(url) != None:
					Usage("wget doesn't retrieve local files")
			if connyAS: systemCall(["osascript", connyAS])
			systemCall([getbin('wget'), "-P", self.getdir] + self.items)
		else: selBrowser(urls=self.items, tb=False, xb=self.xb)
					
	def urlSearch(self):
		if not self.files: self.nt =True
		Urlcollector.urlCollect(self)
		if self.nt: LastExit.termInit(self)
		try:
			if self.items:
				yorn = '%s\nRetrieve the above %s? yes, [No] ' \
				       % ('\n'.join(self.items),
					  sPl(len(self.items),
				          	('url', 'message-id')[self.id])
					 )
				if raw_input(yorn) in ('y', 'Y'):
					if not self.id: self.urlGo()
					else: Kiosk.kioskStore(self)
			else:
				msg = 'No %s found. [Ok] ' \
				      % ('urls', 'message-ids')[self.id]
				raw_input(msg)
		except KeyboardInterrupt: pass
		if self.nt: LastExit.reInit(self)


def run():
	up = Urlbatcher()
	up.argParser()
	up.urlSearch()
