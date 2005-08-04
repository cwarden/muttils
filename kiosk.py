#! /usr/bin/env python
# $Id: kiosk.py,v 1.15 2005/08/04 21:17:26 chris Exp $

###
# needs python version 2.3 #
###

import email, email.Errors, getopt, mailbox, os, re, sys, urllib
from email.Generator import Generator
from email.Parser import HeaderParser
from email.Utils import parseaddr, parsedate
from tempfile import mkstemp
from time import sleep, asctime
if sys.version_info[1] > 3:
	from subprocess import Popen, PIPE
	def subpro(cmd):
		return Popen(cmd, bufsize=1, stdout=PIPE).stdout.readline()
else:
	def subpro(cmd): return os.popen(cmd).readline()
from getbin import getBin
from spl import sPl
try: from conny import pppConnect
except ImportError: pass

ggroups = 'http://groups.google.com/groups?hl=de&'

mutt = getBin(('mutt', 'muttng'))
muttone = "%s -e 'set pager_index_lines=0' " \
	       "-e 'set quit=yes' -e 'bind pager q quit' " \
	       "-e 'push <return>' -f" % mutt

def mutti(id): # uncollapse??
	"""Opens kiosk mailbox and goes to id."""
	return "%s -e 'push <search>\"~i\ \'%s\'\"<return>' -f" \
			% (mutt, id)

def Usage(err=''):
	if err: print err
	print 'Usage:\n' \
      	'%(sn)s [-l][-d <mail hierarchy>[:<mail hierarchy> ...]]' \
		'[-k <mbox>][-m <filemask>][-t] <ID> [<ID> ...]\n' \
      	'%(sn)s [-l][-D <mail hierarchy>[:<mail hierarchy> ...]]' \
		'[-k <mbox>][-m <filemask>][-t] <ID> [<ID> ...]\n' \
      	'%(sn)s -n [-l][-k <mbox>][-t] <ID> [<ID> ...]\n' \
      	'%(sn)s -g [-k <mbox>][-t] <ID> [<ID> ...]\n' \
      	'%(sn)s -b <ID> [<ID> ...]\n' \
      	'%(sn)s -h' \
	      % { 'sn': os.path.basename(sys.argv[0]) }
	sys.exit(2)

def regError(err, pat):
	print '%s in pattern "%s"' % (err, pat)
	sys.exit(2)

def fpError(strerror, fp):
	fp.close()
	print strerror
	sys.exit(2)

def leafDir():
	"""Returns path to directory where leafnode
	stores hard links to all articles."""
	try: leafinfo = subpro("newsq")
	except OSError: return None
	# -> 'Contents of queue in directory /sw/var/spool/news/out.going:\n'
	leafl = leafinfo.split('/')[1:-1]
	# -> ['sw', 'var', 'spool', 'news']
	leafl.insert(0, '/')
	leafl.append('message.id')
	return os.path.join(*leafl)
	# -> '/sw/var/spool/news/message.id'

def mailDir():
	"""Returns either ~/Maildir or ~/Mail
	as first item of a list if they are directories,
	an empty list otherwise."""
	castle = os.environ['HOME']
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
		self.version = "w3m" # works with empty string too
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

class Kiosk:
	"""
	Provides methods to search for and retrieve
	messages via their Message-ID.
	"""
	def __init__(self, items=None):
		if items == None: items = []
		self.items = items      # message-ids to look for
		self.kiosk = ''		# path to kiosk mbox
		self.mask = None	# file mask for mdir (applied to directories too)
		self.nt = 0		# if 1: needs terminal
		self.browse = 0		# browse googlegroups
		self.google = 0		# if 1: just googlegroups
		self.mdirs = mailDir() 	# mailbox hierarchies
		self.local = 0          # local search only
		self.msgs = []          # list of retrieved message objects
		self.tmp = 0            # whether kiosk is a temporary file
		self.muttone = 1        # configure mutt for display of 1 msg only
		self.mdmask = r'^(cur|new|tmp)$'

	def argParser(self):
		try: opts, self.items = getopt.getopt(sys.argv[1:], "bd:D:ghk:lm:nt")
		except getopt.GetoptError, strerror: Usage(strerror)
		for o, a in opts:
			if o == '-b':
				self.browse, self.google, self.mdirs = 1, 1, []
			elif o == '-d':
				self.mdirs = self.mdirs + a.split(':')
			elif o == '-D': self.mdirs = a.split(':')
			elif o == '-g':
				self.google, self.mdirs = 1, []
			elif o == '-h': Usage()
			elif o == '-l': self.local, self.google = 1, 0
			elif o == '-k': self.kiosk = a
			elif o == '-m': self.mask = a
			elif o == '-n': self.mdirs = [] # don't search local mailboxes
			elif o == '-t': self.nt = 1
	
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
		fp = open(self.kiosk, "rb", 1)
		testline = fp.readline()
		fp.close()
		if not testline: return # empty is fine
		test = email.message_from_string(testline)
		if not test.get_unixfrom():
			err = '%s: not a unix mailbox' % self.kiosk
			Usage(err)
		else: self.muttone = 0
		
	def dirTest(self):
		"""Checks whether given directories exist."""
		for dir in self.mdirs:
			if not os.path.isdir(os.path.abspath(os.path.expanduser(dir))):
				print 'Warning! %s: not a directory, skipping' % dir
				self.mdirs.remove(dir)

	def goGoogle(self):
		"""Gets messages from Google Groups."""
		print 'Going google ...'
		try: pppConnect()
		except NameError: pass
		delitems = []
		for item in self.items:
			if not self.browse:
				query = {'selm':item, 'output':'gplain'}
			else: query = {'selm':item}
			params = urllib.urlencode(query)
			url = '%s%s' % (ggroups, params)
			if self.browse:
				cmd = "w3m -T text/html '%s'" % url
				os.system(cmd)
				sys.exit()
			try: fp = urllib.urlopen(url)
			except IOError, strerror: # no connection
				fpError(strerror, fp)
			try: msg = email.message_from_file(fp)
			except email.Errors.MessageParseError, strerror:
				fpError(strerror, fp)
			fp.close()
			if 'message-id' in msg:
				self.msgs.append(msg)
				delitems.append(item)
			else:
				print msg.get_payload(decode=1)
				sleep(5)
				print 'Continuing ...'
		for item in delitems: self.items.remove(item)
	
	def leafSearch(self, leafdir):
		print 'Searching local newsserver ...'
#		for root, dirs, files in os.walk(leafdir):
#			for name in files:
#				if name == self.anglid:
#					return os.path.join(root, name)
		# but this is significantly faster:
		leaflets = os.listdir(leafdir)
		for leaflet in leaflets:
			if not self.items: break
			leaflet = os.path.join(leafdir, leaflet)
			if os.path.isdir(leaflet):
				articles = os.listdir(leaflet)
				for item in self.items:
					anglid = '<%s>' % item
					if anglid in articles:
						print 'retrieving message-id %s' % anglid
						fp = open(os.path.join(leaflet, anglid), "rb")
						try: msg = email.message_from_file(fp)
						except email.Errors.MessageParseError, strerror:
							fpError(strerror, fp)
						fp.close()
						self.msgs.append(msg)
						self.items.remove(item)

	def boxParser(self, path, maildir=0):
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
	
	def mailSearch(self):
		print '%s not on local server.\n' \
		      'Searching local mailboxes ...' \
		      % sPl(len(self.items), 'message')
		for mdir in self.mdirs:
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
						dirlist = os.listdir(path)
						if 'cur' in dirlist and 'new' in dirlist:
							self.boxParser(path, 1)
				for name in files:
					if self.items:
						path = os.path.join(root, name)
						self.boxParser(path)

	def masKompile(self):
		"""Compiles masks to exclude files and directories from search."""
		try:
			if self.mask:
				self.mdmask = re.compile(r'%s|%s' % (self.mdmask, self.mask))
				self.mask = re.compile(r'%s' % self.mask)
			else: self.mdmask = re.compile(r'%s' % self.mdmask)
		except re.error, strerror: regError(strerror, self.mask)


	def kioskStore(self):
		self.items = [nakHead(item) for item in self.items]
		if not self.items: Usage('missing message-ids')
		elif self.browse and len(self.items) == 1: self.goGoogle()
		elif self.browse:
			err = 'Browse 1 url at a time'
			Usage(err)
		firstid = self.items[0]
		self.kioskTest()
		if self.mdirs: self.dirTest()
		if not self.google:
			self.masKompile()
			leafdir = leafDir()
			if leafdir: self.leafSearch(leafdir)
			else: print 'No local news server found.'
			if self.items and self.mdirs:
				self.mailSearch()
				if self.items:
					print '%s not in specified local mailboxes.' \
					      % sPl(len(self.items), 'message')
		if self.items and not self.local: self.goGoogle()
		elif self.items:
			print '%s not found locally' \
				% sPl(len(self.items), 'message')
			sleep(5)
			if not self.msgs: sys.exit(0)
		outfp = open(self.kiosk, "ab")
		g = Generator(outfp, mangle_from_=True, maxheaderlen=0)
		for msg in self.msgs:
			msg.__delitem__('status') # show msg as new in mutt
			msg.__delitem__('xref') # delete server info
			if not msg.get_unixfrom(): msg = mkUnixfrom(msg)
			g.flatten(msg, unixfrom=True)
		outfp.close()
		if len(self.msgs) == 1 and self.muttone:
			cmd = "%s '%s'" % (muttone, self.kiosk)
		else: cmd = "%s '%s'" % (mutti(firstid), self.kiosk)
		if self.nt: cmd = "%s <> %s" % (cmd, os.ctermid())
		os.system(cmd)
		if self.tmp:
			try: os.remove(self.kiosk)
			except OSError: pass # in case mutt already removed the file

def main():
	k = Kiosk()
	k.argParser()
	k.kioskStore()

if __name__ == '__main__': main()
