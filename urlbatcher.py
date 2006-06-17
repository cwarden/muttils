urlbatcher_cset = '$Hg: urlbatcher.py,v$'

###
# Caveat:
# If input is read from stdin, it should be of one type
# (text/plain, text/html, email) because the type detecting
# mechanism is only triggered once.
# However you should be able to run this on all kind of files,
# input is checked anew for each file.
###

from cheutils import selbrowser, spl, systemcall
from tpager.LastExit import LastExit
from Urlcollector import Urlcollector
from kiosk import Kiosk

optstring = 'd:D:hiIk:lnr:w:x'

urlbatcher_help = '''
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
-h (display this help)'''

def userHelp(error=''):
	from cheutils.exnam import Usage
	u = Usage(help=urlbatcher_help, rcsid=urlbatcher_cset)
	u.printHelp(err=error)

def goOnline():
	try:
		from cheutils import conny
		conny.appleConnect()
	except ImportError:
		pass

class UrlbatcherError(Exception):
	'''Exception class for this module.'''

class Urlbatcher(Urlcollector, Kiosk, selbrowser.Browser):
	'''
	Parses input for either web urls or message-ids.
	Browses all urls or creates a message tree in mutt.
	You can specify urls/ids by a regex pattern.
	'''
	def __init__(self):
		selbrowser.Browser.__init__(self) # <- items
		Urlcollector.__init__(self,
				proto='web') # <- (Urlregex, LastExit) proto, decl, items, files, pat
		Kiosk.__init__(self)        # <- kiosk, mhiers, mspool, local, google, xb, tb
		self.getdir = ''            # download in dir via wget

	def argParser(self):
		import getopt, sys
		try:
			opts, self.files = getopt.getopt(sys.argv[1:], optstring)
		except getopt.GetoptError, e:
			raise UrlbatcherError, e
		for o, a in opts:
			if o == '-d': # specific mail hierarchies
				self.proto = 'mid'
				self.mhiers = a.split(':')
			if o == '-D': # specific mail hierarchies, exclude mspool
				self.proto = 'mid'
				self.mspool = False
				self.mhiers = a.split(':')
			if o == '-h':
				userHelp()
			if o == '-i': # look for message-ids
				self.proto = 'mid'
			if o == '-I': # look for declared message-ids
				self.proto = 'mid'
				self.decl = True
			if o == '-k': # mailbox to store retrieved messages
				self.proto = 'mid'
				self.kiosk = a
			if o == '-l': # only local search for message-ids
				self.proto = 'mid'
				self.local = True
			if o == '-n': # don't search local mailboxes
				self.proto = 'mid'
				self.mhiers = None
			if o == '-r':
				self.pat = a
			if o == '-w': # download dir for wget
				from cheutils import filecheck
				getdir = a
				self.getdir = filecheck.fileCheck(getdir,
						spec='isdir', absolute=True)
			if o == '-x': # xbrowser
				self.xb = True

	def urlGo(self):
		if self.getdir:
			from cheutils import getbin
			for url in self.items:
				if selbrowser.local_re.match(url):
					raise UrlbatcherError, \
						'wget does not retrieve local files'
			goOnline()
			systemcall.systemCall(
				[getbin.getBin('wget'), '-P', self.getdir] + self.items)
		else:
			selbrowser.Browser.urlVisit(self)
					
	def urlSearch(self):
		Urlcollector.urlCollect(self)
		if not self.files:
			LastExit.termInit(self)
		if self.items:
			yorn = '%s\nRetrieve the above %s? yes, [No] ' \
			       % ('\n'.join(self.items),
				  spl.sPl(len(self.items),
					('url', 'message-id')[self.proto=='mid'])
				 )
			if raw_input(yorn).lower() in ('y', 'yes'):
				if self.proto != 'mid':
					self.urlGo()
				else:
					Kiosk.kioskStore(self)
		else:
			msg = 'No %s found. [Ok] ' \
			      % ('urls', 'message-ids')[self.proto=='mid']
			raw_input(msg)
		if not self.files:
			LastExit.reInit(self)


def run():
	try:
		up = Urlbatcher()
		up.argParser()
		up.urlSearch()
	except UrlbatcherError, e:
		userHelp(e)
	except KeyboardInterrupt:
		print
		pass
