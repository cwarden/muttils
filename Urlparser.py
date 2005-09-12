#! /usr/bin/env python

# $Id: Urlparser.py,v 1.7 2005/09/12 23:14:22 chris Exp $

import email, email.Errors, os.path, re, sys
from email.Utils import getaddresses
from cStringIO import StringIO
from HTMLParser import HTMLParser, HTMLParseError
from mailbox import PortableUnixMailbox

protos = ('all', 'web', 'http', 'mailto',
	  'ftp', 'finger', 'telnet')

# header lists (to be extended)
searchkeys = ['subject', 'organization',
	      'user-agent', 'x-mailer', 'x-newsreader',
	      'list-id', 'list-subscribe', 'list-unsubscribe',
	      'list-help', 'list-archive', 'list-url',
	      'mailing-list', 'x-habeas-swe-9'] 

refkeys = ['references', 'in-reply-to', 'message-id',
	   'original-message-id']

addrkeys = ['from', 'to', 'reply-to', 'cc',
	    'sender', 'x-sender', 'mail-followup-to',
	    'x-apparently-to',
	    'errors-to', 'x-complaints-to', 'x-beenthere']

quote_re = re.compile(r'^(> ?)+', re.MULTILINE)

def msgFactory(fp):
	try: return email.message_from_file(fp)
	except email.Errors.MessageParseError: return ''

def unQuote(s):
	return quote_re.sub('', s)

class Urlparser(HTMLParser):
	"""
	Subclass of Urlregex.
	Extracts urls from html text
	messages or mailboxes.
	"""
	def __init__(self, proto='all'):
		HTMLParser.__init__(self)
		self.proto = proto
		self.id = 0             # search only for message-ids
		self.url_re = None
		self.items = []
		self.msg = ''
		self.ugly = 0

	def protoTest(self):
		if self.proto in protos: return
		print '%s: invalid protocol specification for %s\n' \
		      'Use one of: %s' \
		      % (self.proto, os.path.basename(sys.argv[0]),
			', '.join(protos))
		sys.exit(2)

	def handle_starttag(self, tag, attrs):
		if tag in ('a', 'img'):
			for name, value in attrs:
				if name in ('href', 'src') \
				and self.url_re.match(value):
					self.items.append(value)
	
	def makeUrlist(self, text):
		self.feed(text)
		self.close()

	def headParser(self, keys):
		for key in keys:
			vals = self.msg.get_all(key)
			if vals:
				pairs = getaddresses(vals)
				urls = [pair[1] for pair in pairs if pair[1]]
				self.items += urls

	def headSearcher(self):
		for key in searchkeys:
			vals = self.msg.get_all(key, [])
			for val in vals:
				urls = [u[0] for u in self.url_re.findall(val)]
				self.items += urls

	def mailDeconstructor(self, s):
		try: self.msg = email.message_from_string(s)
		except email.Errors.MessageParseError: return s
		if not self.msg or not self.msg['Message-ID']: return s
		# else it's a message or a mailbox
		if not self.msg.get_unixfrom():
			sl = self.msgDeconstructor()
		else: # treat s like a mailbox because it might be one
			sl = [] # list of strings to search
			fp = StringIO()
			fp.write(s)
			mbox = PortableUnixMailbox(fp, msgFactory)
			while self.msg != None:
				self.msg = mbox.next()
				if self.msg:
					sl = self.msgDeconstructor(sl)
			fp.close()
		s = '\n'.join(sl)
		return unQuote(s) # get quoted urls spanning more than 1 line

	def msgDeconstructor(self, sl=None):
		if sl == None: sl = []
		if self.id: self.headParser(refkeys)
		elif self.proto in ('all', 'mailto'): self.headParser(addrkeys)
		if not self.id: self.headSearcher()
		for part in self.msg.walk(): # use email.Iterator?
			if part.get_content_maintype() == 'text':
				text = part.get_payload(decode=True)
				subtype = part.get_content_subtype()
				if subtype == 'plain':
					sl.append(text)
				elif subtype.startswith('htm'):
					try: self.makeUrlist(text)
					except HTMLParseError, AssertionError:
						self.ugly = True
						pass
		return sl

# EOF vim:ft=python
