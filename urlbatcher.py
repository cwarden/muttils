urlbatcher_cset = "$Hg: urlbatcher.py,v$"

###
# Caveat:
# If input is read from stdin, it should be of one type
# (text/plain, text/html, email) because the type detecting
# mechanism is only triggered once.
# However you should be able to run this on all kind of files,
# input is checked anew for each file.
###

import getopt, os, sys
from cheutils.spl import sPl
from cheutils.selbrowser import selBrowser, local_re
from cheutils.systemcall import systemCall
from tpager.LastExit import LastExit
from Urlcollector import Urlcollector
from Urlregex import mailCheck, ftpCheck
from kiosk import Kiosk

optstring = "d:D:ghiIk:lnr:Tw:x"

urlbatcher_help = """
[-x][-r <pattern>][file ...]
-w <download dir> [-r <pattern]
-i [-r <pattern>][-k <mbox>][<file> ...]
-I [-r <pattern>][-k <mbox>][<file> ...]
-l [-I][-r <pattern>][-k <mbox>][<file> ...]
-d <mail hierarchy>[:<mail hierarchy>[:...]] \\
            [-l][-I][-r <pattern>][-k <mbox>][<file> ...] 
-D <mail hierarchy>[:<mail hierarchy>[:...]] \\
            [-l][-I][-r <pattern>][-k <mbox>][<file> ...]
-n [-l][-I][-r <pattern>][-k <mbox>][<file> ...] 
-g [-I][-r <pattern>][-k <mbox>][<file> ...]
-h (display this help)"""

def userHelp(error=""):
	from cheutils.exnam import Usage
	u = Usage(help=urlbatcher_help, rcsid=urlbatcher_cset)
	u.printHelp(err=error)

def goOnline():
	try:
		from cheutils.conny import appleConnect
		appleConnect()
	except ImportError:
		pass


class Urlbatcher(Urlcollector, Kiosk, LastExit):
	"""
	Parses input for either web urls or message-ids.
	Browses all urls or creates a message tree in mutt.
	You can specify urls/ids by a regex pattern.
	"""
	def __init__(self):
		Urlcollector.__init__(self, proto="web") # <- nt, proto, id, decl, items, files, pat
		Kiosk.__init__(self)        # <- nt, kiosk, mdirs, local, google, xb, tb
		LastExit.__init__(self)
		self.getdir = ""            # download in dir via wget

	def argParser(self):
		try:
			opts, self.files = getopt.getopt(sys.argv[1:], optstring)
		except getopt.GetoptError, msg:
			userHelp(msg)
		for o, a in opts:
			if o == "-d": # add specific mail hierarchies
				self.id = 1
				self.mdirs = self.mdirs + a.split(":")
				self.getdir = ""
			if o == "-D": # specific mail hierarchies
				self.id = 1
				self.mdirs = a.split(":")
				self.getdir = ""
			if o == "-h":
				userHelp()
			if o == "-g": # go to google directly for message-ids
				self.id, self.google, self.mdirs = 1, 1, []
				self.getdir = ""
			if o == "-i": # look for message-ids
				self.id = 1
				self.getdir = ""
			if o == "-I": # look for declared message-ids
				self.id, self.decl = 1, 1
				self.getdir = ""
			if o == "-k": # mailbox to store retrieved messages
				self.id, self.kiosk = 1, a
				self.getdir = ""
			if o == "-l": # only local search for message-ids
				self.local, self.id = 1, 1
				self.getdir = ""
			if o == "-n": # don't search local mailboxes
				self.id, self.mdirs = 1, []
				self.getdir = ""
			if o == "-r":
				self.pat = a
			if o == "-T": # force new terminal
				self.nt = True
			if o == "-w": # download dir for wget
				self.id = 0
				getdir = a
				self.getdir = os.path.abspath(os.path.expanduser(getdir))
				if not os.path.isdir(self.getdir):
					userHelp("%s: not a directory" % self.getdir)
			if o == "-x": # xbrowser
				self.xb, self.id, self.getdir = 1, 0, ""
			if self.id:
				self.proto = "all"

	def urlGo(self):
		if self.getdir:
			for url in self.items:
				if local_re.search(url) != None:
					userHelp("wget doesn't retrieve local files")
			goOnline()
			systemCall([getbin("wget"), "-P", self.getdir] + self.items)
		else:
			selBrowser(urls=self.items, tb=False, xb=self.xb)
					
	def urlSearch(self):
		if not self.files:
			self.nt =True
		Urlcollector.urlCollect(self)
		if self.nt:
			LastExit.termInit(self)
		try:
			if self.items:
				yorn = "%s\nRetrieve the above %s? yes, [No] " \
				       % ("\n".join(self.items),
					  sPl(len(self.items),
				          	("url", "message-id")[self.id])
					 )
				if raw_input(yorn) in ("y", "Y"):
					if not self.id:
						self.urlGo()
					else:
						Kiosk.kioskStore(self)
			else:
				msg = "No %s found. [Ok] " \
				      % ("urls", "message-ids")[self.id]
				raw_input(msg)
		except KeyboardInterrupt:
			pass
		if self.nt:
			LastExit.reInit(self)


def run():
	up = Urlbatcher()
	up.argParser()
	up.urlSearch()
