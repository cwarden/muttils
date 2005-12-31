kiosk_rcsid = '$Id: kiosk.py,v 1.26 2005/12/31 14:03:11 chris Exp $'

###
# needs python version 2.3 #
###

import email, email.Errors, getopt, mailbox, os, re, sys, urllib
from email.Generator import Generator
from email.Parser import HeaderParser
from email.Utils import parseaddr, parsedate
from tempfile import mkstemp
from time import sleep, asctime
from cheutils.getbin import getBin
from cheutils.readwrite import readLine
from cheutils.selbrowser import selBrowser
from cheutils.spl import sPl
from cheutils.systemcall import systemCall, backQuote
from slrnpy.Leafnode import Leafnode

optstr = "bd:D:ghk:lm:ns:tTx"

ggroups = 'http://groups.google.com/groups?'
mailspool = os.getenv('MAIL')
if not mailspool:
	mailspool = os.path.join('var', 'mail', os.environ["USER"])
	if not os.path.isfile(mailspool): mailspool = None
elif mailspool.endswith('/'): mailspool = mailspool[:-1] # ~/Maildir/-INBOX[/]

connyAS = os.path.join(os.environ["HOME"], 'AS', 'conny.applescript')
if not os.path.exists(connyAS): connyAS = False

mutt = getBin('mutt', 'muttng')
muttone = "%s -e 'set pager_index_lines=0' " \
	       "-e 'set quit=yes' -e 'bind pager q quit' " \
	       "-e 'push <return>' -f" % mutt

def mutti(id): # uncollapse??
	"""Opens kiosk mailbox and goes to id."""
	return "%s -e 'push <search>\"~i\ \'%s\'\"<return>' -f" \
			% (mutt, id)

def Usage(err=''):
	from cheutils.exnam import exNam()
	exe = exNam()
	if err: print >>sys.stderr, '%s: %s' % (exe, err)
	else:
		from cheutils.Rcsparser import Rcsparser
		rcs = Rcsparser(kiosk_rcsid)
		print rcs.getVals(shortv=True)
	sys.exit("""Usage:
%(exe)s [-l][-d <mail hierarchy>[:<mail hierarchy> ...]]' \\
      [-k <mbox>][-m <filemask>][-t] <ID> [<ID> ...]
%(exe)s [-l][-D <mail hierarchy>[:<mail hierarchy> ...]]' \\
      [-k <mbox>][-m <filemask>][-t] <ID> [<ID> ...]
%(exe)s -n [-l][-k <mbox>][-t] <ID> [<ID> ...]
%(exe)s -g [-k <mbox>][-t] <ID> [<ID> ...]
     *** -g: broken because plain text is inaccessible ***
%(exe)s -b <ID> [<ID> ...]
%(exe)s -h (display this help)"""
	% vars () )

def regError(err, pat):
	err = '%s in pattern "%s"' % (err, pat)
	Usage(err)

def fpError(strerror, fp):
	fp.close()
	Usage(strerror)

def mailDir():
	"""Returns either ~/Maildir or ~/Mail
	as first item of a list if they are directories,
	an empty list otherwise."""
	castle = os.environ["HOME"]
	for dir in ('Maildir', 'Mail'):
		d = os.path.join(castle, dir)
		if os.path.isdir(d): return [d]
	return []

def msgFactory(fp):
	try: return HeaderParser().parse(fp)
	except email.Errors.HeaderParseError: return ''

def nakHead(header):
	"""Strips Message-ID header down to pure ID."""
	return header.split('>')[0].split('<')[-1]

### customize user-agent header
class AppURLopener(urllib.FancyURLopener):
	def __init__(self, *args):
		urllib.FancyURLopener.__init__(self, *args)

urllib._urlopener = AppURLopener()
###

def mkUnixfrom(msg):
	"""Creates missing unixfrom."""
	date = None
	if 'received' in msg:
		date = msg['received'].split('; ')[-1]
	else: date = msg.__getitem__('date')
	if date:
		date = asctime(parsedate(date))
		if 'return-path' in msg:
			ufromaddr = msg['return-path'][1:-1]
		else: ufromaddr = parseaddr(msg.get('from', 'nobody'))[1]
		msg.set_unixfrom('From %s  %s' % (ufromaddr, date))
	return msg

class Kiosk(Leafnode):
	"""
	Provides methods to search for and retrieve
	messages via their Message-ID.
	"""
	def __init__(self, items=None, spool=''):
		Leafnode.__init__(self, spool=spool) # <- spool
		if items == None: items = []
		self.items = items      # message-ids to look for
		self.kiosk = ''		# path to kiosk mbox
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
		self.mdmask = r'^(cur|new|tmp)$'
		self.mspool = mailspool

	def argParser(self):
		try: opts, self.items = getopt.getopt(sys.argv[1:], optstr)
		except getopt.GetoptError, strerror: Usage(strerror)
		for o, a in opts:
			if o == '-b':
				self.browse, self.google, self.mdirs = True, True, []
			elif o == '-d':
				self.mdirs = self.mdirs + a.split(':')
			elif o == '-D':
				self.mdirs = a.split(':')
				if self.mspool: self.mspool = None
			elif o == '-g':
				self.browse, self.google, self.mdirs = True, True, []
#                                self.google, self.mdirs = 1, []# temporarily(?) disabled
			elif o == '-h': Usage()
			elif o == '-l': self.local, self.google = True, False
			elif o == '-k': self.kiosk = a
			elif o == '-m': self.mask = a
			elif o == '-n': self.mdirs = [] # don't search local mailboxes
			elif o == '-s': self.spool = a # location of local news spool
			elif o == '-t': self.tb = True # use text browser
			elif o == '-T': self.nt = True # needs terminal
			elif o == '-x': self.xb = True # use xbrowser

	def kioskTest(self):
		"""Provides the path to an mbox file to store retrieved messages."""
		if not self.kiosk:
			self.kiosk = mkstemp('kiosk')[1]
			self.tmp = 1
			return
		self.kiosk = os.path.abspath(os.path.expanduser(self.kiosk))
		if not os.path.exists(self.kiosk): return
		if not os.path.isfile(self.kiosk):
			err = '%s: not a regular file' % self.kiosk
			Usage(err)
		testline = readLine(self.kiosk, "rb")
		if not testline: return # empty is fine
		test = email.message_from_string(testline)
		if not test.get_unixfrom():
			err = '%s: not a unix mailbox' % self.kiosk
			Usage(err)
		else: self.muttone = False

	def dirTest(self):
		"""Checks whether given directories exist."""
		for dir in self.mdirs:
			if not os.path.isdir(os.path.abspath(os.path.expanduser(dir))):
				print 'Warning! %s: not a directory, skipping' % dir
				self.mdirs.remove(dir)

	def makeQuery(self, id):
		"""Reformats Message-ID to google query."""
		if not self.browse:
			query = {'selm': id, 'hl': 'en', 'dmode': 'source'}
		else: query = {'selm': id, 'hl': 'en'}
		params = urllib.urlencode(query)
		return '%s%s' % (ggroups, params)

	def goGoogle(self):
		"""Gets messages from Google Groups."""
		print 'Going google ...'
		self.items = [self.makeQuery(id) for id in self.items]
		if self.browse:
			selBrowser(self.items, self.tb, self.xb)
			sys.exit()
		if connyAS: systemCall(["osascript", connyAS])
		found = []
		for item in self.items:
			try: fp = urllib.urlopen(item)
			except IOError, strerror: # no connection
				fpError(strerror, fp)
			try: msg = email.message_from_file(fp)
			except email.Errors.MessageParseError, strerror:
				fpError(strerror, fp)
			fp.close()
			if 'message-id' in msg:
				found.append(item)
				self.msgs.append(msg)
			else:
				print msg.get_payload(decode=1)
				sleep(5)
				print 'Continuing ...'
		for item in found: self.items.remove(item)

	def leafSearch(self):
		print 'Searching local newsserver ...'
		articles, self.items = Leafnode.idPath(self, self.items, True)
		for article in articles:
			fp = open(article, "rb")
			try: msg = email.message_from_file(fp)
			except email.Errors.MessageParseError, strerror:
				fpError(strerror, fp)
			fp.close()
			self.msgs.append(msg)

	def boxParser(self, path, maildir=False):
		print 'Searching %s ...' % path
		if maildir:
			mbox = mailbox.Maildir(path, msgFactory)
		else:
			fp = open(path, "rb")
			mbox = mailbox.PortableUnixMailbox(fp, msgFactory)
		while True:
			msg = mbox.next()
			if msg == None: break
			msgid = msg.get('message-id','')[1:-1]
			if msgid in self.items:
				self.msgs.append(msg)
				self.items.remove(msgid)
				print 'retrieving Message-ID <%s>' % msgid
				if not self.items: break
		if not maildir: fp.close()

	def walkMdir(self, mdir):
		"""Visits mail hierarchies and parses their mailboxes.
		Detects mbox and Maildir mailboxes."""
		for root, dirs, files in os.walk(mdir):	
			if not self.items: break
			rmdl = [d for d in dirs if self.mdmask.search(d)!=None]
			for d in rmdl: dirs.remove(d)
			if self.mask:
				rmfl = [f for f in files if self.mask.search(f)!=None]
				for f in rmfl: files.remove(f)
			for name in dirs:
				if self.items:
					path = os.path.join(root, name)
					if path != self.mspool:
						dirlist = os.listdir(path)
						if 'cur' in dirlist and 'new' in dirlist:
							self.boxParser(path, True)
			for name in files:
				if self.items:
					path = os.path.join(root, name)
					if path != self.mspool:
						self.boxParser(path)

	def mailSearch(self):
		"""Announces search of mailboxes, searches spool,
		and passes mail hierarchies to walkMdir."""
		print '%s not on local server.\n' \
		      'Searching local mailboxes ...' \
		      % sPl(len(self.items), 'message')
		if self.mspool:
			self.boxParser(self.mspool, os.path.isdir(self.mspool))
		for mdir in self.mdirs: self.walkMdir(mdir)

	def masKompile(self):
		"""Compiles masks to exclude files and directories from search."""
		try:
			if self.mask:
				self.mdmask = re.compile(r'%s|%s' % (self.mdmask, self.mask))
				self.mask = re.compile(r'%s' % self.mask)
			else: self.mdmask = re.compile(r'%s' % self.mdmask)
		except re.error, strerror: regError(strerror, self.mask)

	def kioskStore(self):
		"""Displays messages identified by ID either
		by retrieving them locally or from GoogleGroups
		and opening mutt on the kiosk mailbox -- or
		online with a text browser."""
		self.items = [nakHead(item) for item in self.items]
		if not self.items:
			Usage('needs Message-ID(s) as mandatory argument(s)')
		elif self.browse: self.goGoogle()
		firstid = self.items[0]
		self.kioskTest()
		if self.mdirs: self.dirTest()
		if not self.google:
			self.masKompile()
			if not self.spool: Leafnode.newsSpool(self)
			if self.spool: self.leafSearch()
			else: print 'No local news server found.'
			if self.items and self.mdirs:
				self.mailSearch()
				if self.items:
					print '%s not in specified local mailboxes.' \
					      % sPl(len(self.items), 'message')
#                if self.items and not self.local: self.goGoogle()
#                elif self.items:
                if self.items: # haven't found a way to retrieve orig msgs
			print '%s not found' \
				% sPl(len(self.items), 'message')
			if self.msgs: sleep(5)
		if not self.msgs: sys.exit()
		outfp = open(self.kiosk, "ab")
		g = Generator(outfp, maxheaderlen=0)
		for msg in self.msgs:
			msg.__delitem__('status') # show msg as new in mutt
			msg.__delitem__('xref') # delete server info
			if not msg.get_unixfrom(): msg = mkUnixfrom(msg)
			g.flatten(msg, unixfrom=True)
		outfp.close()
		if len(self.msgs) == 1 and self.muttone:
			cmd = "%s '%s'" % (muttone, self.kiosk)
		else: cmd = "%s '%s'" % (mutti(firstid), self.kiosk)
		if self.nt:
			tty = os.ctermid()
			cmd = "%(cmd)s <%(tty)s >%(tty)s" % {'cmd':cmd, 'tty':tty}
		systemCall(cmd, sh=True)
		if self.tmp and os.path.isfile(self.kiosk):
			os.remove(self.kiosk)


def run():
	k = Kiosk()
	k.argParser()
	k.kioskStore()
