kiosk_cset = "$Hg: kiosk.py,v$"

###
# needs python version 2.3 #
###

import email, os, re, time, urllib, sys
from email.Errors import MessageParseError, HeaderParseError
from email.Generator import Generator
from email.Parser import HeaderParser
from email import Utils
from mailbox import Maildir, PortableUnixMailbox
from cheutils import filecheck, readwrite, spl, systemcall
from slrnpy.Leafnode import Leafnode, LeafnodeError

optstr = "bd:D:hk:lm:ns:tx"
ggroups = "http://groups.google.com/groups?"
muttone = "-e 'set pager_index_lines=0' " \
       "-e 'set quit=yes' -e 'bind pager q quit' " \
       "-e 'push <return>' -f"

kiosk_help = """
[-l][-d <mail hierarchy>[:<mail hierarchy> ...]]' \\
      [-k <mbox>][-m <filemask>][-t] <ID> [<ID> ...]
[-l][-D <mail hierarchy>[:<mail hierarchy> ...]]' \\
      [-k <mbox>][-m <filemask>][-t] <ID> [<ID> ...]
-n [-l][-k <mbox>][-t] <ID> [<ID> ...]
-b <ID> [<ID> ...]
-h (display this help)"""

def userHelp(error=""):
	from cheutils.exnam import Usage
	u = Usage(help=kiosk_help, rcsid=kiosk_cset)
	u.printHelp(err=error)

def mailSpool(mailspool=None):
	"""Tries to return a sensible default for user's mail spool.
	Returns None otherwise."""
	mailspool = os.getenv("MAIL")
	if not mailspool:
		ms = os.path.join("var", "mail", os.environ["USER"])
		if os.path.isfile(ms):
			return ms
	elif mailspool.endswith(os.sep):
		return mailspool[:-1] # ~/Maildir/-INBOX[/]
	return mailspool

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

def makeQuery(id):
	"""Reformats Message-ID to google query."""
	query = {"selm": id, "hl": "en"}
	params = urllib.urlencode(query)
	return "%s%s" % (ggroups, params)

def msgFactory(fp):
	try:
		return HeaderParser().parse(fp)
	except HeaderParseError:
		return ""

def nakHead(header):
	"""Strips Message-ID header down to pure ID."""
	return header.split("<")[-1].strip(">")

def muttI(id): # uncollapse??
	"""Opens kiosk mailbox and goes to id."""
	return "-e 'set uncollapse_jump' " \
		"-e 'push <search>~i\ %s<return>' -f" \
		% id

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
			ufromaddr = Utils.parseaddr(
					msg.get("from", "nobody"))[1]
		msg.set_unixfrom("From %s  %s" % (ufromaddr, date))
	return msg


class KioskError(Exception):
	"""Exception class for kiosk."""

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
		self.browse = False	# limit to browse googlegroups
		self.mdirs = [] 	# mailbox hierarchies
		self.local = False      # limit to local search
		self.msgs = []          # list of retrieved message objects
		self.tmp = False        # whether kiosk is a temporary file
		self.muttone = True     # configure mutt for display of 1 msg only
		self.xb = False	        # force x-browser
		self.tb = False         # use text browser
		self.mspool = True	# look for MID in default mailspool
		self.mdmask = r"^(cur|new|tmp)$"

	def argParser(self):
		import getopt
		from Urlregex import Urlregex
		try:
			opts, args = getopt.getopt(sys.argv[1:], optstr)
		except getopt.GetoptError, e:
			raise KioskError, e
		for o, a in opts:
			if o == "-b":
				self.browse, self.mdirs = True, False
			if o == "-d": # specific mail hierarchies
				self.mdirs = a.split(":")
			if o == "-D": # specific mail hierarchies, exclude mspool
				self.mdirs, self.mspool = a.split(":"), False
			if o == "-h":
				userHelp()
			if o == "-l":
				self.local = True
			if o == "-k":
				self.kiosk = a
			if o == "-m":
				self.mask = a
			if o == "-n":
				self.mdirs = False # don"t search local mailboxes
			if o == "-s":
				self.spool = a # location of local news spool
			if o == "-t":
				self.tb = True # use text browser
			if o == "-x":
				self.xb = True # use xbrowser
		ur = Urlregex()
		ur.id = True
		ur.findUrls(" ".join(args))
		if ur.items:
			self.items = ur.items
		else:
			raise KioskError, "no valid Message-ID found"

	def kioskTest(self):
		"""Provides the path to an mbox file to store retrieved messages."""
		if not self.kiosk:
			import tempfile
			self.kiosk = tempfile.mkstemp("kiosk")[1]
			self.tmp = 1
			return
		self.kiosk = filecheck.absolutePath(self.kiosk)
		if not os.path.exists(self.kiosk):
			return
		if not os.path.isfile(self.kiosk):
			raise KioskError, "%s: not a regular file" \
					% self.kiosk
		testline = readwrite.readLine(self.kiosk, "rb")
		if not testline:
			return # empty is fine
		test = email.message_from_string(testline)
		if not test.get_unixfrom():
			raise KioskError, "%s: not a unix mailbox" \
					% self.kiosk
		else:
			self.muttone = False

	def dirTest(self):
		"""Checks whether given directories exist."""
		for dir in self.mdirs:
			if not os.path.isdir(filecheck.absolutePath(dir)):
				print "Warning! %s: not a directory, skipping" % dir
				self.mdirs.remove(dir)

	def goGoogle(self, quit=False):
		"""Gets messages from Google Groups."""
		from cheutils import selbrowser
		print "Going google ..."
		self.items = [makeQuery(id) for id in self.items]
		selbrowser.selBrowser(self.items,
				tb=self.tb, xb=self.xb)
		if quit:
			sys.exit()

	def leafSearch(self):
		print "Searching local newsserver ..."
		articles, self.items = Leafnode.idPath(self,
				idlist=self.items, verbose=True)
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
			try:
				msg = mbox.next()
			except IOError, e:
				print e
				break
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
			self.mspool = mailSpool()
			self.boxParser(self.mspool, os.path.isdir(self.mspool))
		for mdir in self.mdirs:
			self.walkMdir(mdir)

	def masKompile(self):
		"""Compiles masks to exclude files and directories from search."""
		try:
			if self.mask:
				self.mdmask = re.compile(r"%s|%s" \
						% (self.mdmask, self.mask))
				self.mask = re.compile(r"%s" % self.mask)
			else:
				self.mdmask = re.compile(r"%s" \
						% self.mdmask)
		except re.error, e:
			raise KioskError, "%s in pattern `%s'" \
					% (e, self.mask)

	def openKiosk(self, firstid):
		"""Opens mutt on kiosk mailbox."""
		from cheutils import getbin
		mutt = getbin.getBin("mutt", "muttng")
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
			cmd = "%s %s '%s'" % (mutt, muttone, self.kiosk)
		else:
			cmd = "%s %s '%s'" % (mutt, muttI(firstid), self.kiosk)
		if self.nt:
			tty = os.ctermid()
			cmd = "%(cmd)s <%(tty)s >%(tty)s" % vars()
		systemcall.systemCall(cmd, sh=True)
		if self.tmp and os.path.isfile(self.kiosk):
			os.remove(self.kiosk)

	def kioskStore(self):
		"""Collects messages identified by ID either
		by retrieving them locally or from GoogleGroups."""
		if not self.items:
			raise KioskError, "need Message-ID(s) as argument(s)"
		self.items = [nakHead(item) for item in self.items]
		if self.browse:
			self.goGoogle(quit=True)
		self.kioskTest()
		itemscopy = self.items[:]
		if not self.spool:
			try:
				Leafnode.newsSpool(self)
			except LeafnodeError, e:
				print e
		if self.spool:
			self.leafSearch()
		else:
			print "No local news server found."
		if self.items and self.mdirs != False:
			if not self.mdirs:
				self.mdirs = mailDir()
			self.dirTest()
			self.masKompile()
			self.mailSearch()
			if self.items:
				print "%s not in specified local mailboxes." \
				      % spl.sPl(len(self.items), "message")
                if self.items:
			print "%s not found" \
				% spl.sPl(len(self.items), "message")
			if self.msgs:
				itemscopy = [id for id in itemscopy \
						if id not in self.items]
				time.sleep(3)
			if not self.local:
				self.goGoogle(quit=False)
		if self.msgs:
			self.openKiosk(itemscopy[0])


def run():
	k = Kiosk()
	try:
		k.argParser()
		k.kioskStore()
	except KioskError, e:
		userHelp(e)
	except KeyboardInterrupt:
		print
		pass
