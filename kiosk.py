kiosk_cset = '$Hg: kiosk.py,v$'

###
# needs python version 2.3 #
###

import email, os, re, time, urllib, urllib2, sys
from email.Generator import Generator
from email.Parser import HeaderParser
from email.Errors import MessageParseError, HeaderParseError
from mailbox import Maildir, PortableUnixMailbox
from cheutils import filecheck, readwrite, spl, systemcall
from cheutils.html2text import HTML2Text

optstr = 'bd:D:hk:lm:ntx'
ggroups = 'http://groups.google.com/groups'
useragent = ('User-Agent', 'w3m')
urlfailmsg = 'reason of url retrieval failure: '
urlerrmsg = 'url retrieval error code: '
changedsrcview = 'source view format changed at Google'
muttone = "-e 'set pager_index_lines=0' " \
       "-e 'set quit=yes' -e 'bind pager q quit' " \
       "-e 'push <return>' -f"

kiosk_help = '''
[-l][-d <mail hierarchy>[:<mail hierarchy> ...]]' \\
      [-k <mbox>][-m <filemask>][-t] <ID> [<ID> ...]
[-l][-D <mail hierarchy>[:<mail hierarchy> ...]]' \\
      [-k <mbox>][-m <filemask>][-t] <ID> [<ID> ...]
-n [-l][-k <mbox>][-t] <ID> [<ID> ...]
-b <ID> [<ID> ...]
-h (display this help)'''

def userHelp(error=''):
	from cheutils.exnam import Usage
	u = Usage(help=kiosk_help, rcsid=kiosk_cset)
	u.printHelp(err=error)

def mailSpool():
	'''Tries to return a sensible default for user's mail spool.
	Returns None otherwise.'''
	mailspool = os.getenv('MAIL')
	if not mailspool:
		ms = os.path.join('var', 'mail', os.environ['USER'])
		if os.path.isfile(ms):
			return ms
	elif mailspool.endswith(os.sep):
		return mailspool[:-1] # ~/Maildir/-INBOX[/]
	return mailspool

def mailHier():
	'''Returns either ~/Maildir or ~/Mail
	as first item of a list if they are directories,
	an empty list otherwise.'''
	castle = os.environ['HOME']
	for md in ('Maildir', 'Mail'):
		d = os.path.join(castle, md)
		if os.path.isdir(d):
			return [d]
	return []

def msgFactory(fp):
	try:
		p = HeaderParser()
		return p.parse(fp)
	except (HeaderParseError, MessageParseError):
		return ''

def goOnline():
	try:
		from cheutils import conny
		conny.appleConnect()
	except ImportError:
		pass

def muttI(mid): # uncollapse??
	'''Opens kiosk mailbox and goes to mid.'''
	return "-e 'set uncollapse_jump' " \
		"-e 'push <search>~i\ \'%s\'<return>' -f" \
		% mid

def mkUnixfrom(msg):
	'''Creates missing unixfrom.'''
	date = None
	if 'received' in msg:
		date = msg['received'].split('; ')[-1]
	else:
		date = msg.__getitem__('date')
	if date:
		try:
			date = time.asctime(email.Utils.parsedate(date))
		except TypeError:
			# don't punish wrong date format (very old msgs)
			pass
		else:
			if 'return-path' in msg:
				ufrom = msg['return-path'][1:-1]
			else:
				ufrom = email.Utils.parseaddr(
						msg.get('from', 'nobody'))[1]
			msg.set_unixfrom('From %s  %s' % (ufrom, date))
	return msg


class KioskError(Exception):
	'''Exception class for kiosk.'''

class Kiosk(object):
	'''
	Provides methods to search for and retrieve
	messages via their Message-ID.
	'''
	def __init__(self, items=None):
		if items == None:
			items = []
		self.items = items      # message-ids to look for
		self.kiosk = ''		# path to kiosk mbox
		self.mask = None	# file mask for mdir (applied to directories too)
		self.browse = False	# limit to browse googlegroups
		self.mhiers = [] 	# mailbox hierarchies
		self.local = False      # limit to local search
		self.msgs = []          # list of retrieved message objects
		self.muttone = True     # configure mutt for display of 1 msg only
		self.xb = False	        # force x-browser
		self.tb = False         # use text browser
		self.mspool = True	# look for MID in default mailspool
		self.mdmask = '^(cur|new|tmp)$'

	def argParser(self):
		import getopt
		from Urlregex import Urlregex
		try:
			opts, args = getopt.getopt(sys.argv[1:], optstr)
		except getopt.GetoptError, e:
			raise KioskError, e
		for o, a in opts:
			if o == '-b':
				self.browse, self.mhiers = True, None
			if o == '-d': # specific mail hierarchies
				self.mhiers = a.split(':')
			if o == '-D': # specific mail hierarchies, exclude mspool
				self.mhiers, self.mspool = a.split(':'), False
			if o == '-h':
				userHelp()
			if o == '-l':
				self.local = True
			if o == '-k':
				self.kiosk = a
			if o == '-m':
				self.mask = a
			if o == '-n':
				self.mhiers = None # don't search local mailboxes
			if o == '-t':
				self.tb = True # use text browser
			if o == '-x':
				self.xb = True # use xbrowser
		ur = Urlregex(proto='mid', uniq=False)
		ur.findUrls(' '.join(args))
		if ur.items:
			self.items = ur.items
		else:
			raise KioskError, 'no valid Message-ID found'

	def kioskTest(self):
		'''Provides the path to an mbox file to store retrieved messages.'''
		if not self.kiosk:
			import tempfile
			self.kiosk = tempfile.mkstemp('.kiosk')[1]
			return
		self.kiosk = filecheck.absolutePath(self.kiosk)
		if not os.path.isfile(self.kiosk):
			raise KioskError, '%s: not a regular file' \
					% self.kiosk
		if not os.path.exists(self.kiosk) \
				or not os.path.getsize(self.kiosk):
			# non existant or empty is fine
			return
		e = '%s: not a unix mailbox' % self.kiosk
		testline = readwrite.readLine(self.kiosk, 'rb')
		try:
			test = email.message_from_string(testline)
		except MessageParseError:
			raise KioskError, e
		if test.get_unixfrom():
			self.muttone = False
		else:
			raise KioskError, e

	def hierTest(self):
		'''Checks whether given directories exist and
		creates mhiers set (unique elems) with absolute paths.'''
		if not self.mhiers:
			self.mhiers = mailHier()
		mhiers = set(self.mhiers)
		self.mhiers = set([])
		for hier in mhiers:
			abshier = filecheck.fileCheck(hier, spec='isdir',
					absolute=True, noexit=False)
			if abshier:
				self.mhiers.add(abshier)
			else:
				print "Warning! `%s': not a directory, skipping" \
						% hier

	def makeQuery(self, mid):
		'''Reformats Message-ID to google query.'''
		query = ({'selm': mid, 'dmode': 'source'},
				{'selm': mid})[self.browse]
		return '%s?%s' % (ggroups,  urllib.urlencode(query))

	def gooBrowse(self):
		'''Visits given urls with browser and exits.'''
		from cheutils import selbrowser
		urls = [self.makeQuery(mid) for mid in self.items]
		selbrowser.selBrowser(urls,
				tb=self.tb, xb=self.xb)
		sys.exit()

	def gooRetrieve(self, mid, found,
			opener, htparser, header_re):
		try:
			fp = opener.open(self.makeQuery(mid))
			htparser.write(fp.read(), append=False)
			fp.close()
			liniter = iter(htparser.readlines(nl=False))
		except urllib2.URLError, e:
			if hasattr(e, 'reason'):
				raise KioskError, urlfailmsg + e
			if hasattr(e, 'code'):
				raise KioskError, urlerrmsg + e
		line = ''
		try:
			while not header_re.match(line):
				line = liniter.next()
		except StopIteration:
			print '%s: not at Google' % mid
			time.sleep(5)
		else:
			lines = [line]
			try:
				while not line.startswith('(image) Google Home['):
					line = liniter.next()
					lines.append(line)
			except StopIteration:
				print '\n'.join(lines)
				raise KioskError, changedsrcview
			msg = '\n'.join(lines[:-1])
			msg = email.message_from_string(msg)
			found.append(mid)
			self.msgs.append(msg)

	def goGoogle(self):
		'''Gets messages from Google Groups.'''
		print 'Going google ...'
		if self.browse:
			self.gooBrowse()
		print '*Unfortunately Google masks all email addresses*'
		opener = urllib2.build_opener()
		opener.addheaders = [useragent]
		htparser = HTML2Text(strict=False)
		header_re = re.compile(r'[A-Z][-a-zA-Z]+: ')
		goOnline()
		found = []
		for mid in self.items:
			self.gooRetrieve(mid, found,
					opener, htparser, header_re)
		htparser.close()
		self.items = [mid for mid in self.items if not mid in found]

	def leafSearch(self):
		try:
			from slrnpy.Leafnode import Leafnode
		except ImportError:
			return
		leafnode = Leafnode()
		print 'Searching local newsserver ...'
		articles, self.items = leafnode.idPath(idlist=self.items,
				verbose=True)
		for article in articles:
			fp = open(article, 'rb')
			try:
				msg = email.message_from_file(fp)
			except MessageParseError, e:
				raise KioskError, e
			fp.close()
			self.msgs.append(msg)
		if self.items:
			print '%s not on local server' \
			      % spl.sPl(len(self.items), 'message')

	def boxParser(self, path, maildir=False, isspool=False):
		if not isspool and path == self.mspool or \
				self.mask and \
				self.mask.search(path) != None:
			return
		if maildir:
			dl = os.listdir(path)
			for d in 'cur', 'new':
				if not d in dl:
					return
			mbox = Maildir(path, msgFactory)
		else:
			try:
				fp = open(path, 'rb')
			except IOError, e:
				print e
				return
			mbox = PortableUnixMailbox(fp, msgFactory)
		print 'Searching %s ...' % path
		while True:
			try:
				msg = mbox.next()
			except IOError, e:
				print e
				break
			if msg == None:
				break
			msgid = msg.get('message-id','')[1:-1]
			if msgid in self.items:
				self.msgs.append(msg)
				self.items.remove(msgid)
				print 'retrieving Message-ID <%s>' % msgid
				if not self.items:
					break
		if not maildir:
			fp.close()

	def walkMhier(self, mdir):
		'''Visits mail hierarchies and parses their mailboxes.
		Detects mbox and Maildir mailboxes.'''
		for root, dirs, files in os.walk(mdir):	
			if not self.items:
				break
			rmdl = [d for d in dirs if self.mdmask.search(d)!=None]
			for d in rmdl:
				dirs.remove(d)
			for name in dirs:
				if self.items:
					path = os.path.join(root, name)
					self.boxParser(path, True)
			for name in files:
				if self.items:
					path = os.path.join(root, name)
					self.boxParser(path)

	def mailSearch(self):
		'''Announces search of mailboxes, searches spool,
		and passes mail hierarchies to walkMhier.'''
		print 'Searching local mailboxes ...'
		if self.mspool:
			self.mspool = mailSpool()
			self.boxParser(self.mspool,
					os.path.isdir(self.mspool),
					isspool=True)
		self.mdmask = re.compile(r'%s' % self.mdmask)
		for mhier in self.mhiers:
			self.walkMhier(mhier)

	def masKompile(self):
		try:
			self.mask = re.compile(r'%s' % self.mask)
		except re.error, e:
			raise KioskError, "%s in pattern `%s'" \
					% (e, self.mask)

	def openKiosk(self, firstid):
		'''Opens mutt on kiosk mailbox.'''
		from cheutils import getbin
		mutt = getbin.getBin('mutt', 'muttng')
		outfp = open(self.kiosk, 'ab')
		g = Generator(outfp, maxheaderlen=0)
		for msg in self.msgs:
			# delete read status and local server info
			for h in ('Status', 'Xref'):
				msg.__delitem__(h)
			if not msg.get_unixfrom():
				msg = mkUnixfrom(msg)
			g.flatten(msg, unixfrom=True)
		outfp.close()
		cmd = "%s %s '%s'"
		if len(self.msgs) == 1 and self.muttone:
			cmd = cmd % (mutt, muttone, self.kiosk)
		else:
			cmd = cmd % (mutt, muttI(firstid), self.kiosk)
		if not os.isatty(0):
			tty = os.ctermid()
			cmd = '%(cmd)s <%(tty)s >%(tty)s' % vars()
		systemcall.systemCall(cmd, sh=True)

	def kioskStore(self):
		'''Collects messages identified by ID either
		by retrieving them locally or from GoogleGroups.'''
		if not self.items:
			raise KioskError, 'need Message-ID(s) as argument(s)'
		if self.browse:
			self.goGoogle()
		self.kioskTest()
		if self.mask:
			self.masKompile()
		itemscopy = self.items[:]
		self.leafSearch()
		if self.items and self.mhiers != None:
			self.hierTest()
			self.mailSearch()
			if self.items:
				print '%s not in specified local mailboxes.' \
				      % spl.sPl(len(self.items), 'message')
                if self.items:
			print '%s not found' \
				% spl.sPl(len(self.items), 'message')
			if not self.local:
				self.goGoogle()
			else:
				time.sleep(3)
		if self.msgs:
			firstid = None
			for mid in itemscopy:
				if not mid in self.items:
					firstid = mid
					break
			self.openKiosk(firstid)


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
