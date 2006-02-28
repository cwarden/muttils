urlpager_cset = "$Hg: urlpager.py,v$"

###
# Caveat:
# If input is read from stdin, it should be of one type
# (text/plain, text/html, email) because the type detecting
# mechanism is only triggered once.
# However you should be able to run this on all kind of files,
# input is checked anew for each file.
###

import os, readline
from tpager.LastExit import LastExit
from tpager.Tpager import Tpager
from cheutils.getbin import getBin
from cheutils.selbrowser import selBrowser, local_re
from cheutils.systemcall import systemCall
from Urlcollector import Urlcollector
from Urlregex import mailCheck, ftpCheck
from kiosk import Kiosk

optstring = "bd:D:f:ghiIlnp:k:r:tTw:x"
mailers = ("mutt", "pine", "elm", "mail") 

urlpager_help = """
[-p <protocol>][-r <pattern>][-t][-x][-f <ftp client>][<file> ...]
-w <download dir> [-r <pattern]
-i [-r <pattern>][-k <mbox>][<file> ...]
-I [-r <pattern>][-k <mbox>][<file> ...]
-l [-I][-r <pattern>][-k <mbox>][<file> ...]
-d <mail hierarchy>[:<mail hierarchy>[:...]] \\
            [-I][-l][-r <pattern>][-k <mbox>][<file> ...]
-D <mail hierarchy>[:<mail hierarchy>[:...]] \\
            [-I][-l][-r <pattern>][-k <mbox>][<file> ...]
-n [-r <pattern][-I][-l][-k <mbox>][<file> ...]
-g [-r <pattern][-I][-k <mbox>][<file> ...]
-b [-r <pattern][-I][<file> ...]
-h (display this help)"""

def userHelp(error=""):
	from cheutils.exnam import Usage
	u = Usage(help=urlpager_help, rcsid=urlpager_cset)
	u.printHelp(err=error)

def goOnline():
	try:
		from cheutils.conny import appleConnect
		appleConnect()
	except ImportError:
		pass


class Urlpager(Urlcollector, Kiosk, Tpager, LastExit):
	def __init__(self):
		Urlcollector.__init__(self) # <- nt, proto, id, laxid, items, files, pat
		Kiosk.__init__(self) # <- browse, google, nt, kiosk, mdirs, local, xb, tb
		Tpager.__init__(self, name="url") # <- items, name
		LastExit.__init__(self)
		self.ft = ""	   # ftpclient
		self.url = ""	   # selected url
		self.getdir = ""   # download in dir via wget

	def argParser(self):
		from sys import argv
		from getopt import getopt, GetoptError
		try:
			opts, self.files = getopt(argv[1:], optstring)
		except GetoptError, e:
			userHelp(e)
		for o, a in opts:
			if o == "-b": # don't look up msgs locally
				self.browse, self.id, self.google = True, True, True
				self.mdirs = []
				self.getdir = ""
			if o == "-d": # add specific mail hierarchies
				self.id = True
				self.mdirs = self.mdirs + a.split(":")
				self.getdir = ""
			if o == "-D": # specific mail hierarchies
				self.id = True
				self.mdirs = a.split(":")
				self.getdir = ""
			if o == "-f": # ftp client
				self.ft = getBin(a)
			if o == "-g": # don't look up msgs locally
				self.id, self.google = True, True
				self.mdirs = []
			if o == "-h": userHelp()
			if o == "-I": # look for declared message-ids
				self.id, self.decl = True, True
				self.getdir = ""
			if o == "-i": # look for ids, in text w/o prot (email false positives)
				self.id = True
				self.getdir = ""
			if o == "-k": # mailbox to store retrieved message
				self.id = True
				self.kiosk = a
				self.getdir = ""
			if o == "-l": # only local search for message-ids
				self.local, self.id = True, True
				self.getdir = ""
			if o == "-n": # don't search mailboxes for message-ids
				self.id = True
				self.mdirs = []
				self.getdir = ""
			if o == "-p": # protocol(s)
				self.proto = a
				self.id = False
			if o == "-r": # regex pattern to match urls against
				self.pat = a
			if o == "-x": # xbrowser
				self.xb = True
			if o == "-t": # text browser command
				self.tb = True
			if o == "-T": # needs terminal (at end of pipe e.g)
				self.nt = True
			if o == "-w": # download dir for wget
				self.proto = "web"
				self.getdir = a
				self.getdir = os.path.abspath(os.path.expanduser(self.getdir))
				if not os.path.isdir(self.getdir):
					userHelp("%s: not a directory" % self.getdir)
				self.id = False

	def urlPager(self):
		if not self.id and self.proto != "all":
			self.name = "%s %s" % (self.proto, self.name)
		elif self.id: self.name = "message-id"
		self.name = "unique %s" % self.name
		self.url = Tpager.interAct(self)

	def urlGo(self):
		cs = []
		conny = local_re.search(self.url) == None
		if self.proto == "mailto" \
		or self.proto == "all" and mailCheck(self.url):
			cs = [getBin(mailers)]
			conny = False
		elif self.getdir:
			if not conny:
				userHelp("wget doesn't retrieve local files")
			cs = [getBin("wget"), "-P", self.getdir]
		elif self.proto == "ftp" or self.ft or ftpCheck(self.url):
			if not os.path.splitext(self.url)[1] \
			and not self.url.endswith("/"):
				self.url = self.url + "/"
			if not self.ft: cs = ["ftp"]
			else: cs = [self.ft]
			self.nt = True
		if not cs:
			selBrowser(self.url, tb=self.tb, xb=self.xb)
		else:
			if conny:
				goOnline()
			if not self.getdir or self.nt: # program needs terminal
				tty = os.ctermid()
				cs = cs + [self.url, "<", tty, ">", tty]
				cs = " ".join(cs)
				systemCall(cs, sh=True)
			else:
				cs.append(self.url)
				systemCall(cs)

	def urlSearch(self):
		if not self.files: self.nt = True
		issue = Urlcollector.urlCollect(self)
		if issue:
			userHelp(issue)
		if self.nt:
			LastExit.termInit(self)
		self.urlPager()
		if self.url:
			if not self.id:
				self.urlGo()
			else:
				self.items = [self.url]
				Kiosk.kioskStore(self)
		if self.nt:
			try:
				LastExit.reInit(self)
			except IndexError:
				pass


def run():
	up = Urlpager()
	try:
		up.argParser()
		up.urlSearch()
	except KeyboardInterrupt:
		pass
