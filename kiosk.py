#! /usr/bin/env python
# $Id: kiosk.py,v 1.8 2005/06/27 19:27:39 chris Exp $

###
# needs python version 2.3 #
###

import email, email.Errors, getopt, mailbox, os, re, sys, tempfile, urllib
from email.Generator import Generator
from time import sleep, strftime
from Urlregex import mail_re
from getbin import getBin
from spl import sPl
try: from conny import pppConnect
except ImportError: pass

ggroups = 'http://groups.google.com/groups?hl=de&'

mutt = getBin(('mutt', 'muttng'))
muttone = "%s -e 'set pager_index_lines=0' " \
	       "-e 'set quit=yes' -e 'bind pager q quit' " \
	       "-e 'push <return>' -f" % mutt
#from_re = re.compile('[-._a-z9-9]+@[-._a-z0-9]+', re.IGNORECASE)

def Usage(err=''):
	if err: print err
	print 'Usage:\n' \
      	'%(sn)s [-l][-d <mail hierarchy>[:<mail hierarchy> ...]][-k <mbox>][-m <filemask>][-t] <msgID> [<msgID> ...]\n' \
      	'%(sn)s [-l][-D <mail hierarchy>[:<mail hierarchy> ...]][-k <mbox>][-m <filemask>][-t] <msgID> [<msgID> ...]\n' \
      	'%(sn)s -n [-l][-k <mbox>][-t] <msgID> [<msgID> ...]\n' \
      	'%(sn)s -g [-k <mbox>][-t] <msgID> [<msgID> ...]\n' \
      	'%(sn)s -b <msgID> [<msgID> ...]\n' \
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
	leafinfo = os.popen("newsq").readline()
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
	try: return email.message_from_file(fp)
	except email.Errors.MessageParseError: return ''

def mailboxTest(path):
	fp = open(path, "rb")
	msg = msgFactory(fp)
	fp.close()
	if msg: return msg.get_unixfrom()

def nakHead(header):
	return header.split('>')[0].split('<')[-1]

### customize user-agent header
class AppURLopener(urllib.FancyURLopener):
	def __init__(self, *args):
		self.version = "w3m" # works with empty string too
		urllib.FancyURLopener.__init__(self, *args)

urllib._urlopener = AppURLopener()
###


class Kiosk:
	def __init__(self):
		self.items = []		# message-ids to look for
		self.kiosk = ''		# path to kiosk mbox
		self.mask = ''		# file mask for mdir (applied to directories too)
		self.nt = 0		# if 1: needs terminal
		self.browse = 0		# browse googlegroups
		self.google = 0		# if 1: just googlegroups
		self.mdirs = mailDir() 	# mailbox hierarchies
		self.local = 0          # local search only
		self.msgs = []
		self.tmp = 0

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
		if not self.kiosk:
			self.kiosk = tempfile.mkstemp('kiosk')[1]
			self.tmp = 1
			return
		self.kiosk = os.path.abspath(os.path.expanduser(self.kiosk))
		if not os.path.exists(self.kiosk): return
		if not os.path.isfile(self.kiosk):
			err = '%s: not a regular file' % self.kiosk
			Usage(err)
		fp = open(self.kiosk)
		testline = fp.readline()
		fp.close()
		if not testline: return # empty is fine
		test = email.message_from_string(testline)
		if not test.get_unixfrom():
			err = '%s: not a unix mailbox' % self.kiosk
			Usage(err)
		
	def mdirTest(self):
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
		for id in self.items:
			if not self.browse:
				query = {'selm':id, 'output':'gplain'}
			else: query = {'selm':id}
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
			if msg.__getitem__('message-id'):
				self.msgs.append(msg)
				delitems.append(id)
			else:
				print msg.get_payload(decode=1)
				sleep(5)
				print 'Continuing ...'
		for id in delitems: self.items.remove(id)
	
	def leafSearch(self):
		print 'Searching local newsserver ...'
		leafdir = leafDir()
#		for root, dirs, files in os.walk(leafdir):
#			for name in files:
#				if name == self.anglid:
#					return os.path.join(root, name)
		# but this is significantly faster:
		leaflets = os.listdir(leafdir)
		urldict = {}
		[urldict.setdefault(id, '<%s>' % id) for id in self.items]
		for leaflet in leaflets:
			leaflet = os.path.join(leafdir, leaflet)
			if self.items and os.path.isdir(leaflet):
				articles = os.listdir(leaflet)
				found = []
				for key in urldict:
					anglid = urldict[key]
					if anglid in articles:
						fp = open(os.path.join(leaflet, anglid))
						try: msg = email.message_from_file(fp)
						except email.Errors.MessageParseError, strerror:
							fpError(strerror, fp)
						fp.close()
						self.msgs.append(msg)
						found.append(key)
						self.items.remove(key)
						print 'found message-id <%s>' % key
				for key in found: del urldict[key]

	def boxParser(self, path, maildir=0):
		print 'Searching %s ...' % path
		if maildir:
			mbox = mailbox.Maildir(path, msgFactory)
		else:
			fp = open(path)
			mbox = mailbox.PortableUnixMailbox(fp, msgFactory)
		msg = ''
		while msg != None and self.items:
			msg = mbox.next()
			if msg:
				try:
					msgid = msg.__getitem__('message-id')[1:-1]
					if msgid in self.items:
						self.msgs.append(msg)
						self.items.remove(msgid)
						print 'retrieved message-id <%s>' % msgid
				except TypeError: pass # in rarest case of no id (None)
		if not maildir: fp.close()
	
	def mailSearch(self):
		print '%s not on local server.\n' \
		      'Searching local mailboxes ...' \
		      % sPl(len(self.items), 'message')
		for mdir in self.mdirs:
			for root, dirs, files in os.walk(mdir):	
				if self.mask:
					rmdl = [d for d in dirs if not self.mask.search(d)]
					for name in rmdl:
						if name in dirs: dirs.remove(name)
				for name in dirs:
					if not self.items: break
					dir = os.path.join(root, name)
					dirlist = os.listdir(dir)
					if 'cur' in dirlist and 'new' in dirlist:
						self.boxParser(dir, 1)
						dirs.remove(name)
				for name in files:
					if self.items and (not self.mask or self.mask.search(name)):
						path = os.path.join(root, name)
						self.boxParser(path)

	def kioskStore(self):
		self.items = [nakHead(id) for id in self.items]
		if not self.items: Usage('missing message-ids')
		elif self.browse and len(self.items) == 1: self.goGoogle()
		elif self.browse:
			err = 'Browse 1 url at a time'
			Usage(err)
		self.kioskTest()
		if self.mdirs: self.mdirTest()
		if not self.google:
			self.leafSearch()
			if self.items and self.mdirs:
				if self.mask:
					try: self.mask = re.compile(r'%s' % self.mask)
					except re.error, strerror:
						regError(strerror, self.mask)
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
		outfp = open(self.kiosk, "a")
		g = Generator(outfp)
		for msg in self.msgs:
			if not msg.get_unixfrom():
				From = msg.__getitem__('From')
				From = mail_re.search(From).group(0)
				date = strftime("%a %b %d %H:%M:%S %Y")
				msg.set_unixfrom('From %s  %s' % (From, date))
			g.flatten(msg, unixfrom=True)
		outfp.close()
		if len(self.msgs) == 1: cmd = "%s '%s'" % (muttone, self.kiosk)
		else: cmd = "%s -zf '%s'" % (mutt, self.kiosk)
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
