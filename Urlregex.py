#! /usr/bin/env python
Urlregex_rcsid = '$Id: Urlregex.py,v 1.14 2005/08/21 20:18:10 chris Exp $'

import os.path, re, sys
from HTMLParser import HTMLParseError
from Urlparser import Urlparser
from Rcsparser import Rcsparser
from unilist import uniList_o

def orJoin(s):
	return '(%s)' % '|'.join(s.split())

# and now to the url parts
#any = '_a-z0-9/#~:.?+=&%!@\-'   # valid url-chars
any = '-._a-z0-9/#~:,?+=&%!@()' # valid url-chars + comma + parenthesises
			        # Message-ID: <10rb6mngqccs018@corp.supernews.com>
                                # Message-id: <20050702131039.GA10840@oreka.com>
idy = '-._a-z0-9#~?+=&%!$\]['   # valid message-id-chars ### w/o ":/"?
punc = '-.,:?!'		        # punctuation (how 'bout "!"?)

# top level domains
tops = "a[cdefgilmnoqrstuwz] b[abdefghijmnorstvwyz] " \
	"c[acdfghiklmnoruvxyz] d[ejkmoz] e[ceghrst] " \
	"f[ijkmor] g[abdefghilmnpqrstuwy] " \
	"h[kmnrtu] i[delnmoqrst] j[emop " \
	"k[eghimnprwyz] l[abcikrstuvy] " \
	"m[acdghklmnopqrstuvwxyz] n[acefgilopruz] om " \
	"p[aefghklmnrstwy] qa r[eouw] " \
	"s[abcdeghijklmnortuvyz] " \
	"t[cdfghjkmnoprtvwz] u[agkmsyz] " \
	"v[acegivu] w[fs] y[etu] z[amw] " \
	"arpa com edu gov int mil net org aero biz coop info name pro"
top = '\.%s' % orJoin(tops)

### outro ###
outro = r"""
	%(top)s			# top level preceded by dot
	(			# { ungreedy 0 or more
		/		#   slash
		[%(any)s] *	#   0 or more valid  
	) ?			# } 0 or one
	(?=			# look-ahead non-consumptive assertion
		[%(punc)s]*	#  either 0 or more punctuation
		[^%(any)s]	#  followed by a non-url char
	|			# or else
		$		#  then end of the string
	)
	""" % vars()

### outro w/ spaces ###
spoutro = r"""
	%(top)s			# top level dom preceded by dot
	(			# { 0 or more
		\s*/		#   opt space and slash
		[%(any)s\s]*	#   any or space (space to be removed)
	) ?			# } 0 or one
	(?=>)		# lookahead for ">"
	""" % vars()

# get rid of *quoted* mail headers of no use
# (how to do this more elegantly?)
headers = "Received References Message-ID In-Reply-To " \
	"Delivered-To List-Id Path Return-Path " \
	"Newsgroups NNTP-Posting-Host Xref " \
	"X-ID X-Abuse-Info X-Trace X-MIME-Autoconverted"
head = orJoin(headers)

headsoff = r"""
	(?<=			# look back in negative anger
		[\n^]		#  for newline or absolute beginning
	)			# end anger
	%s:			# header followed by colon &
	  	[^\n]+		# greedy anything
	(			# { 0 or more
		\n		#   newline followed by
		[ \t]+		#   greedy spacetabs
		[^\n]+		#   greedy anything
	) *			# } 0 or more
	(\n|$)			# newline or end of text
	""" % head

# attributions:
nproto = '(msgid|news|nntp|message(-id)?|article|MID)(:\s*|\s+)<{,2}'

mid = r"""
	[%(idy)s]+              # one or more valid id char
	@
	[-._a-z0-9]+ 		# one or more server char
	%(top)s                 # top level domain
	\b
	""" % vars()

declid = r'(%(nproto)s%(mid)s)' % vars()
simplid = r'(\b%s)' % mid

rawwipe = r'(%s)|(%s)' % (declid, headsoff)

## precompiled regexes ##
ftp_re = re.compile('ftp(://|\.)', re.IGNORECASE)
mail_re = re.compile(r'(mailto:)?[-._a-z0-9]+@[-._a-z0-9]+%s\b' \
		    % top, re.IGNORECASE)
	
## filter functions ##

def mailKill(url):
	return not mail_re.match(url)

def ftpCheck(url):
	return ftp_re.match(url)

def httpCheck(url):
	return not mail_re.match(url) and not ftp_re.match(url)

def mailCheck(url):
	return mail_re.match(url)

filterdict = {	'web':	mailKill,
		'ftp':	ftpCheck,
		'http':	httpCheck,
		'mailto': mailCheck }

class Urlregex(Urlparser):
	"""
	Provides functions to extract urls from text,
	customized by attributes.
	Detects also www-urls that don't start with a protocol
	and urls spanning more than 1 line
	if they are enclosed in "<>".
	"""
	def __init__(self, proto='all', nofind=0):
		Urlparser.__init__(self, proto) # <- id, proto, items, url_re, ugly
		self.nofind = nofind    # for grabbing regexes only
		self.decl = 0		# list only declared urls
		self.uni = 1		# list only unique urls
		self.kill_re = None	# customized pattern to find non url chars
		self.intro = ''
		self.protocol = ''	# pragmatic proto (may include www., ftp.)
		self.proto_re = None

	def httpAdd(self, url):
		if not re.match(self.protocol, url):
			return 'http://%s' % url
		return url

	def urlCheck(self, s):
		self.urlObjects()
		url = self.kill_re.sub('', s)
		return self.url_re.match(url)


	def setStrings(self):
		### intro ###
		if self.proto in ('all', 'web'): ## groups
			protocols = "(www|ftp)\. https?:// " \
				"finger:// ftp:// telnet:// mailto:".split()
#                                "(file://(localhost)?/|http://(localhost|127\.) " \
				# TO DO: local switch!
			# gopher? wais?
			if self.proto == 'web':
				protocols = protocols[:-1] # web only
			intros = '%s' % '|'.join(protocols)
			protocols = '%s' % '|'.join(protocols[1:])
			self.intro = '(%s)' % intros
			self.protocol = '(%s)' % protocols

		else:				  ## singles
			self.decl = 1
			if self.proto != 'mailto':
				self.protocol = '%s://' % self.proto
			else: self.protocol = 'mailto:'
			if self.proto == 'http':
				self.intro = '(https?://|www\.)'
			elif self.proto == 'ftp':
				self.intro = 'ftp(://|\.)'
			else: self.intro = self.protocol
		self.intro = '(url:)?%s' % self.intro

	def getRaw(self):

		proto_url = r"""	## long url ##
			(?<=<)		# look behind for "<"
			%(intro)s	# intro
			[%(any)s\s] +	# any or space (space to be removed)
			%(spoutro)s     # outro w/ spaces
			|		## or url in 1 line ##
			\b		# start at word boundary
			%(intro)s	# intro
			[%(any)s] +?	# followed by 1 or more valid url char
			%(outro)s	# outro
			""" % { 'intro':   self.intro,
			        'any':     any,
                                'spoutro': spoutro,
				'outro':   outro }

		if self.decl: return '(%s)' % proto_url

		## follows an attempt to comprise as much urls as possible
		## some bad formatted stuff too
		any_url = r"""		## long url ##
			(?<=<)		# look behind for "<"
			[%(any)s\s] +	# any or space (space to be removed)
			%(spoutro)s     # outro w/ spaces
			|		## or url in 1 line ##
			\b		# start at word boundary
			[%(any)s] +?	# one or more valid characters
			%(outro)s	# outro
			""" % { 'any':     any,
				'spoutro': spoutro,
				'outro':   outro }
		
		return '(%s|%s)' % (proto_url, any_url)

	def uniDeluxe(self):
		"""remove duplicates deluxe:
		of http://www.blacktrash.org, www.blacktrash.org
		keep only the first, declared version."""
		truncs = [self.proto_re.sub('', u) for u in self.items]
		deluxurls = []
		for i in range(len(self.items)):
			url = self.items[i]
			trunc = truncs[i]
			if truncs.count(trunc) == 1 \
			or len(url) > len(trunc):
				deluxurls.append(url)
		self.items = deluxurls

	def urlFilter(self):
		if not self.decl and self.proto in filterdict:
			self.items = filter(filterdict[self.proto], self.items)
		if self.uni:
			self.items = uniList_o(self.items)
			if not self.id and not self.decl:
				self.uniDeluxe()

	def urlObjects(self):
		"""Creates customized regex objects of url."""
		Urlparser.protoTest(self)
		if not self.id:
			self.setStrings()
			rawurl = self.getRaw()
			self.url_re = re.compile(rawurl, re.IGNORECASE|re.VERBOSE)
			if not self.nofind:
				self.kill_re = re.compile('\s+|^url:', re.IGNORECASE) 
				if not self.decl:
					self.proto_re = re.compile('^%s' % self.protocol, re.I)
		elif self.decl:
			self.url_re = re.compile(declid, re.IGNORECASE|re.VERBOSE)
			if not self.nofind: self.kill_re = re.compile(nproto, re.I)
		else: self.url_re = re.compile(simplid, re.IGNORECASE|re.VERBOSE)

	def findUrls(self, data, type='text/plain'):
		self.urlObjects() # compile url_re
		if type == 'text/plain':
			s = Urlparser.mailDeconstructor(self, data)
			if not self.id:
				wipe_re = re.compile(rawwipe, re.IGNORECASE|re.VERBOSE)
				s = wipe_re.sub('', s)
			urls = [u[0] for u in self.url_re.findall(s)]
			if self.kill_re: urls = [self.kill_re.sub('', u) for u in urls]
			if urls: self.items += urls
		elif type == 'text/html':
			try: Urlparser.makeUrlist(self, data)
			except HTMLParseError, AssertionError:
				self.ugly = 1
				pass
		self.urlFilter()


def _test():
	rcs = Rcsparser(Urlregex_rcsid)
	sample = """hello world, these are 3 urls:
cis.tarzisius.net
www.python.org.
<www.black
trash.org> Can you find them?"""
	print rcs.getVals()
	print sample
	ur = Urlregex()
	ur.findUrls(sample)
	print "Here's what we found: '%s'" % ur.items

if __name__ == '__main__': _test()
