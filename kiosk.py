kiosk_cset = "$Hg$"

###
# needs python version 2.3 #
###

import email, os, re, time, urllib
from email.Errors import MessageParseError, HeaderParseError
from email.Generator import Generator
from email.Parser import HeaderParser
from email import Utils
from mailbox import Maildir, PortableUnixMailbox
from cheutils import getbin, readwrite, selbrowser, spl, systemcall
from slrnpy.Leafnode import Leafnode

optstr = "bd:D:ghk:lm:ns:tx"

ggroups = "http://groups.google.com/groups?"
mailspool = os.getenv("MAIL")
if not mailspool:
	mailspool = os.path.join("var", "mail", os.environ["USER"])
	if not os.path.isfile(mailspool):
		mailspool = None
elif mailspool.endswith("/"):
	mailspool = mailspool[:-1] # ~/Maildir/-INBOX[/]

mutt = getbin.getBin("mutt", "muttng")
muttone = "%s -e 'set pager_index_lines=0' " \
	       "-e 'set quit=yes' -e 'bind pager q quit' " \
	       "-e 'push <return>' -f" % mutt

def mutti(id): # uncollapse??
	"""Opens kiosk mailbox and goes to id."""
	return "%s -e 'push <search>\"~i\ \'%s\'\"<return>' -f" \
			% (mutt, id)

def goOnline():
	try:
		from cheutils import conny
		conny.appleConnect()
	except ImportError:
		pass

kiosk_help = """
[-l][-d <mail hierarchy>[:<mail hierarchy> ...]]' \\
      [-k <mbox>][-m <filemask>][-t] <ID> [<ID> ...]
[-l][-D <mail hierarchy>[:<mail hierarchy> ...]]' \\
      [-k <mbox>][-m <filemask>][-t] <ID> [<ID> ...]
-n [-l][-k <mbox>][-t] <ID> [<ID> ...]
-g [-k <mbox>][-t] <ID> [<ID> ...]
     *** -g: broken because plain text is inaccessible ***
-b <ID> [<ID> ...]
-h (display this help)"""

def userHelp(error=""):
	from cheutils.exnam import Usage
	u = Usage(help=kiosk_help, rcsid=kiosk_cset)
	u.printHelp(err=error)

def regError(err, pat):
	err = "%s in pattern `%s'" % (err, pat)
	userHelp(err)

def mailDir():
	"""Returns either ~/Maildir or ~/Mail
	as first item of a list if they are directories,
	an empty list otherwise."""
	castle = os.environ["HOME"]
	for dir in ("Maildir", "Mail"):
		d = os.path.join(castle, dir)
		if os.path.isdir(d):
			return [d]
	return []

def msgFactory(fp):
	try:
		return HeaderParser().parse(fp)
	except HeaderParseError:
		return ""

def nakHead(header):
	"""Strips Message-ID header down to pure ID."""
	return header.split("<")[-1].strip(">")

def mkUnixfrom(msg):
	"""Creates missing unixfrom."""
	date = None
	if "received" in msg:
		date = msg["received"].split("; ")[-1]
	else:
		date = msg.__getitem__("date")
	if date:
		date = time.asctime(Utils.parsedate(date))
		if "return-path" in msg:
			ufromaddr = msg["return-path"][1:-1]
		else:
			ufromaddr = Utils.parseaddr(msg.get("from", "nobody"))[1]
		msg.set_unixfrom("From %s  %s" % (ufromaddr, date))
	return msg


class KioskError(Exception):
	"""Exception class for kiosk."""

### customize user-agent header
class AppURLopener(urllib.FancyURLopener):
	def __init__(self, *args):
		urllib.FancyURLopener.__init__(self, *args)

urllib._urlopener = AppURLopener()
###

class Kiosk(Leafnode):
	"""
	Provides methods to search for and retrieve
	messages via their Message-ID.
	"""
	def __init__(self, items=None, spool=""):
		Leafnode.__init__(self, spool=spool) # <- spool
		if items == None:
			items = []
		self.items = items      # message-ids to look for
		self.kiosk = ""		# path to kiosk mbox
		self.mask = None	# file mask for mdir (applied to directories too)
		self.nt = False		# if True: needs terminal
		self.browse = False	# browse googlegroups
		self.google = False	# if True: just googlegroups
		self.mdirs = mailDir() 	# mailbox hierarchies
		self.local = False      # local search only
		self.msgs = []          # list of retrieved message objects
		self.tmp = False        # whether kiosk is a temporary file
		self.muttone = True     # configure mutt for display of 1 msg only
		self.xb = False	        # force x-browser
		self.tb = False         # use text browser
		self.mdmask = r"^(cur|new|tmp)$"
		self.mspool = mailspool

	def argParser(self):
		import getopt, sys
		try:
			opts, self.items = getopt.getopt(sys.argv[1:], optstr)
		except GetoptError, e:
			userHelp(e)
		for o, a in opts:
			if o == "-b":
				self.browse, self.google, self.mdirs = True, True, []
			if o == "-d":
				self.mdirs = self.mdirs + a.split(":")
			if o == "-D":
				self.mdirs = a.split(":")
				if self.mspool:
					self.mspool = None
			if o == "-g":
				self.browse, self.google, self.mdirs = True, True, []
#                                self.google, self.mdirs = 1, []# temporarily(?) disabled
			if o == "-h":
				userHelp()
			if o == "-l":
				self.local, self.google = True, False
			if o == "-k":
				self.kiosk = a
			if o == "-m":
				self.mask = a
			if o == "-n":
				self.mdirs = [] # don"t search local mailboxes
			if o == "-s":
				self.spool = a # location of local news spool
			if o == "-t":
				self.tb = True # use text browser
			if o == "-x":
				self.xb = True # use xbrowser

	def kioskTest(self):
		"""Provides the path to an mbox file to store retrieved messages."""
		if not self.kiosk:
			import tempfile
			self.kiosk = tempfile.mkstemp("kiosk")[1]
			self.tmp = 1
			return
		self.kiosk = os.path.abspath(os.path.expanduser(self.kiosk))
		if not os.path.exists(self.kiosk):
			return
		if not os.path.isfile(self.kiosk):
			userHelp("%s: not a regular file" % self.kiosk)
		testline = readwrite.readLine(self.kiosk, "rb")
		if not testline:
			return # empty is fine
		test = email.message_from_string(testline)
		if not test.get_unixfrom():
			userHelp("%s: not a unix mailbox" % self.kiosk)
		else:
			self.muttone = False

	def dirTest(self):
		"""Checks whether given directories exist."""
		for dir in self.mdirs:
			if not os.path.isdir(os.path.abspath(os.path.expanduser(dir))):
				print "Warning! %s: not a directory, skipping" % dir
				self.mdirs.remove(dir)

	def makeQuery(self, id):
		"""Reformats Message-ID to google query."""
		if not self.browse:
			query = {"selm": id, "hl": "en", "dmode": "source"}
		else:
			query = {"selm": id, "hl": "en"}
		params = urllib.urlencode(query)
		return "%s%s" % (ggroups, params)

	def goGoogle(self):
		"""Gets messages from Google Groups."""
		print "Going google ..."
		self.items = [self.makeQuery(id) for id in self.items]
		if self.browse:
			import sys
			selbrowser.selBrowser(self.items, self.tb, self.xb)
			sys.exit()
		goOnline()
		found = []
		for item in self.items:
			fp = urllib.urlopen(item)
			try:
				msg = email.message_from_file(fp)
			except (IOError, MessageParseError), e: # IOError: no connection
				raise KioskError, e
			fp.close()
			if "message-id" in msg:
				found.append(item)
				self.msgs.append(msg)
			else:
				print msg.get_payload(decode=1)
				time.sleep(5)
				print "Continuing ..."
		for item in found:
			self.items.remove(item)

	def leafSearch(self):
		print "Searching local newsserver ..."
		articles, self.items = Leafnode.idPath(self, self.items, True)
		for article in articles:
			fp = open(article, "rb")
			try:
				msg = email.message_from_file(fp)
			except MessageParseError, e:
				raise KioskError, e
			fp.close()
			self.msgs.append(msg)

	def boxParser(self, path, maildir=False):
		print "Searching %s ..." % path
		if maildir:
			mbox = Maildir(path, msgFactory)
		else:
			fp = open(path, "rb")
			mbox = PortableUnixMailbox(fp, msgFactory)
		while True:
			msg = mbox.next()
			if msg == None:
				break
			msgid = msg.get("message-id","")[1:-1]
			if msgid in self.items:
				self.msgs.append(msg)
				self.items.remove(msgid)
				print "retrieving Message-ID <%s>" % msgid
				if not self.items:
					break
		if not maildir:
			fp.close()

	def walkMdir(self, mdir):
		"""Visits mail hierarchies and parses their mailboxes.
		Detects mbox and Maildir mailboxes."""
		for root, dirs, files in os.walk(mdir):	
			if not self.items:
				break
			rmdl = [d for d in dirs if self.mdmask.search(d)!=None]
			for d in rmdl:
				dirs.remove(d)
			if self.mask:
				rmfl = [f for f in files if self.mask.search(f)!=None]
				for f in rmfl: files.remove(f)
			for name in dirs:
				if self.items:
					path = os.path.join(root, name)
					if path != self.mspool:
						dirlist = os.listdir(path)
						if "cur" in dirlist and "new" in dirlist:
							self.boxParser(path, True)
			for name in files:
				if self.items:
					path = os.path.join(root, name)
					if path != self.mspool:
						self.boxParser(path)

	def mailSearch(self):
		"""Announces search of mailboxes, searches spool,
		and passes mail hierarchies to walkMdir."""
		print "%s not on local server.\n" \
		      "Searching local mailboxes ..." \
		      % spl.sPl(len(self.items), "message")
		if self.mspool:
			self.boxParser(self.mspool, os.path.isdir(self.mspool))
		for mdir in self.mdirs:
			self.walkMdir(mdir)

	def masKompile(self):
		"""Compiles masks to exclude files and directories from search."""
		try:
			if self.mask:
				self.mdmask = re.compile(r"%s|%s" % (self.mdmask, self.mask))
				self.mask = re.compile(r"%s" % self.mask)
			else:
				self.mdmask = re.compile(r"%s" % self.mdmask)
		except re.error, e:
			regError(e, self.mask)

	def openKiosk(self):
		"""Opens mutt on kiosk mailbox."""
		outfp = open(self.kiosk, "ab")
		g = Generator(outfp, maxheaderlen=0)
		for msg in self.msgs:
			msg.__delitem__("status") # show msg as new in mutt
			msg.__delitem__("xref") # delete server info
			if not msg.get_unixfrom():
				msg = mkUnixfrom(msg)
			g.flatten(msg, unixfrom=True)
		outfp.close()
		if len(self.msgs) == 1 and self.muttone:
			cmd = "%s '%s'" % (muttone, self.kiosk)
		else:
			cmd = "%s '%s'" % (mutti(firstid), self.kiosk)
		if self.nt:
			tty = os.ctermid()
			cmd = "%(cmd)s <%(tty)s >%(tty)s" % vars()
		systemcall.systemCall(cmd, sh=True)
		if self.tmp and os.path.isfile(self.kiosk):
			os.remove(self.kiosk)

	def kioskStore(self):
		"""Collects messages identified by ID either
		by retrieving them locally or from GoogleGroups."""
		self.items = [nakHead(item) for item in self.items]
		if not self.items:
			userHelp("needs Message-ID(s) as mandatory argument(s)")
		elif self.browse:
			self.goGoogle()
		firstid = self.items[0]
		self.kioskTest()
		if self.mdirs:
			self.dirTest()
		if not self.google:
			self.masKompile()
			if not self.spool:
				Leafnode.newsSpool(self)
			if self.spool:
				self.leafSearch()
			else:
				print "No local news server found."
			if self.items and self.mdirs:
				self.mailSearch()
				if self.items:
					print "%s not in specified local mailboxes." \
					      % spl.sPl(len(self.items), "message")
#                if self.items and not self.local: self.goGoogle()
#                elif self.items:
                if self.items: # haven"t found a way to retrieve orig msgs
			print "%s not found" \
				% spl.sPl(len(self.items), "message")
			if self.msgs:
				time.sleep(5)
		if self.msgs:
			self.openKiosk()


def run():
	k = Kiosk()
	try:
		k.argParser()
		k.kioskStore()
	except KeyboardInterrupt:
		pass
