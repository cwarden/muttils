urlpager_rcsid = '$Id: urlpager.py,v 1.5 2005/12/29 17:59:10 chris Exp $'

###
# Caveat:
# If input is read from stdin, it should be of one type
# (text/plain, text/html, email) because the type detecting
# mechanism is only triggered once.
# However you should be able to run this on all kind of files,
# input is checked anew for each file.
###

import getopt, os, readline, sys
from tpager.LastExit import LastExit
from tpager.Tpager import Tpager
from cheutils.getbin import getBin
from cheutils.selbrowser import selBrowser, local_re
from cheutils.systemcall import systemCall
from Urlcollector import Urlcollector
from Urlregex import mailCheck, ftpCheck
from kiosk import Kiosk

optstring = "bd:D:f:ghiIlnp:k:r:tTw:x"
mailers = ('mutt', 'pine', 'elm', 'mail') 
connyAS = os.path.join(os.environ["HOME"], 'AS', 'conny.applescript')
if not os.path.exists(connyAS): connyAS = False

def Usage(msg=''):
	exe = os.path.basename(sys.argv[0])
	if msg: print >>sys.stderr, '%s: %s' (exe, msg)
	else:
		from cheutils.Rcsparser import Rcsparser
		rcs = Rcsparser(urlpager_rcsid)
		print rcs.getVals(shortv=True)
	sys.exit("""Usage:
%(exe)s [-p <protocol>][-r <pattern>][-t][-x][-f <ftp client>][<file> ...]
%(exe)s -w <download dir> [-r <pattern]
%(exe)s -i [-r <pattern>][-k <mbox>][<file> ...]
%(exe)s -I [-r <pattern>][-k <mbox>][<file> ...]
%(exe)s -l [-I][-r <pattern>][-k <mbox>][<file> ...]
%(exe)s -d <mail hierarchy>[:<mail hierarchy>[:...]] \\
            [-I][-l][-r <pattern>][-k <mbox>][<file> ...]
%(exe)s -D <mail hierarchy>[:<mail hierarchy>[:...]] \\
            [-I][-l][-r <pattern>][-k <mbox>][<file> ...]
%(exe)s -n [-r <pattern][-I][-l][-k <mbox>][<file> ...]
%(exe)s -g [-r <pattern][-I][-k <mbox>][<file> ...]
%(exe)s -b [-r <pattern][-I][<file> ...]
%(exe)s -h (display this help)"""
		% { 'exe': exe })


class Urlpager(Urlcollector, Kiosk, Tpager, LastExit):
	def __init__(self):
		Urlcollector.__init__(self) # <- nt, proto, id, laxid, items, files, pat
		Kiosk.__init__(self) # <- browse, google, nt, kiosk, mdirs, local, xb, tb
		Tpager.__init__(self, name='url') # <- items, name
		LastExit.__init__(self)
		self.ft = ''	   # ftpclient
		self.url = ''	   # selected url
		self.getdir = ''   # download in dir via wget

	def argParser(self):
		try: opts, self.files = getopt.getopt(sys.argv[1:], optstring)
		except getopt.GetoptError, msg: Usage(msg)
		for o, a in opts:
			if o == '-b': # don't look up msgs locally
				self.browse, self.id, self.google = True, True, True
				self.mdirs = []
				self.getdir = ''
			elif o == '-d': # add specific mail hierarchies
				self.id = True
				self.mdirs = self.mdirs + a.split(':')
				self.getdir = ''
			elif o == '-D': # specific mail hierarchies
				self.id = True
				self.mdirs = a.split(':')
				self.getdir = ''
			elif o == '-f': # ftp client
				self.ft = getBin(a)
			elif o == '-g': # don't look up msgs locally
				self.id, self.google = True, True
				self.mdirs = []
			elif o == '-h': Usage()
			elif o == '-I': # look for declared message-ids
				self.id, self.decl = True, True
				self.getdir = ''
			elif o == '-i': # look for ids, in text w/o prot (email false positives)
				self.id = True
				self.getdir = ''
			elif o == '-k': # mailbox to store retrieved message
				self.id = True
				self.kiosk = a
				self.getdir = ''
			elif o == '-l': # only local search for message-ids
				self.local, self.id = True, True
				self.getdir = ''
			elif o == '-n': # don't search mailboxes for message-ids
				self.id = True
				self.mdirs = []
				self.getdir = ''
			elif o == '-p': # protocol(s)
				self.proto = a
				self.id = False
			elif o == '-r': # regex pattern to match urls against
				self.pat = a
			elif o == '-x': # xbrowser
				self.xb = True
			elif o == '-t': # text browser command
				self.tb = True
			elif o == '-T': # needs terminal (at end of pipe e.g)
				self.nt = True
			elif o == '-w': # download dir for wget
				self.proto = 'web'
				self.getdir = a
				self.getdir = os.path.abspath(os.path.expanduser(self.getdir))
				if not os.path.isdir(self.getdir):
					Usage('%s: not a directory' % self.getdir)
				self.id = False

	def urlPager(self):
		if not self.id and self.proto != 'all':
			self.name = '%s %s' % (self.proto, self.name)
		elif self.id: self.name = 'message-id'
		self.name = 'unique %s' % self.name
		self.url = Tpager.interAct(self)

	def urlGo(self):
		cs = []
		conny = local_re.search(self.url) == None
		if self.proto == 'mailto' \
		or self.proto == 'all' and mailCheck(self.url):
			cs = [getBin(mailers)]
			conny = False
		elif self.getdir:
			if not conny:
				Usage("wget doesn't retrieve local files")
			cs = [getBin('wget'), "-P", self.getdir]
		elif self.proto == 'ftp' or self.ft or ftpCheck(self.url):
			if not os.path.splitext(self.url)[1] \
			and not self.url.endswith('/'):
				self.url = self.url + '/'
			if not self.ft: cs = ["ftp"]
			else: cs = [self.ft]
			self.nt = True
		if not cs: selBrowser(self.url, tb=self.tb, xb=self.xb)
		else:
			if conny and connyAS: systemCall(["osascript", connyAS])
			if not self.getdir or self.nt: # program needs terminal
				tty = os.ctermid()
				cs = cs + [self.url, "<", tty, ">", tty]
				cs = ' '.join(cs)
				systemCall(cs, sh=True)
			else:
				cs.append(self.url)
				systemCall(cs)

	def urlSearch(self):
		if not self.files: self.nt = True
		result = Urlcollector.urlCollect(self)
		if result: Usage(result)
		if self.nt: LastExit.termInit(self)
		try:
			self.urlPager()
			if self.url:
				if not self.id: self.urlGo()
				else:
					self.items = [self.url]
					Kiosk.kioskStore(self)
		except KeyboardInterrupt: pass
		if self.nt: LastExit.reInit(self)


def run():
	up = Urlpager()
	up.argParser()
	up.urlSearch()
