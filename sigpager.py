#!/usr/bin/env python

sigpager_rcsid = '$Id: sigpager.py,v 1.8 2005/09/05 15:27:06 chris Exp $'

# Caveat:
# Try the -n option if you send stdout to a tty

import getopt, os, re, readline, sys
from random import shuffle
from LastExit import LastExit
from Rcsparser import Rcsparser
from Tpager import Tpager
from readwrite import readFile, writeFile

# defaults:
sigdir = os.path.expanduser('~/.Sig')
defaultsig = os.getenv('SIGNATURE')
if not defaultsig:
	defaultsig = os.path.expanduser('~/.signature')
optstring = "d:fhns:t:w"
# d: sigdir, f [include separator], h [help], n [needs terminal],
# s: defaultsig, t: sigtail, w [(over)write target file(s)]

def Usage(msg=''):
	rcs = Rcsparser(sigpager_rcsid)
	print rcs.getVals(shortv=True)
	if msg: print msg
	print 'Usage:\n' \
	'%(fn)s [-d <sigdir>][-f][-n][-s <defaultsig>]' \
		'[-t <sigtail>][-]\n' \
	'%(fn)s [-d <sigdir>][-f][-n][-s <defaultsig>]' \
		'[-t <sigtail>][-w][<file> ...]\n' \
	'%(fn)s -h' % {'fn': rcs.rcsdict['rcsfile']}
	sys.exit(2)

class Signature(Tpager, LastExit):
	"""
	Provides functions to interactively choose a mail signature
	matched against a regular expression of your choice.
	"""
	def __init__(self):
		Tpager.__init__(self,name='sig',format='bf',qfunc='default sig',ckey='/')
							# <- item, name, format, qfunc
		LastExit.__init__(self)
		self.sign = ''          # chosen self.signature
		self.sig = defaultsig	# self.signature file
		self.sdir = sigdir	# directory containing sigfiles
		self.tail = '.sig'	# tail for sigfiles
		self.full = 0		# sig including separator
		self.nt = 0		# if 1: needs terminal (stdout to a tty)
		self.inp = ''		# append sig at input
		self.targets = []	# target files to self.sign
		self.w = "wa"           # if "w": overwrite target file(s)
					# sig appended otherwise
		self.pat = ''           # match sigs against pattern
		self.menu = 'Enter pattern to match signatures against:\n'

	def argParser(self):
		try: opts, args = getopt.getopt(sys.argv[1:], optstring)
		except getopt.GetoptError, msg: Usage(msg)
		for o, a in opts:
			if o == '-d': self.sdir = a
			elif o == '-f': self.full = 1
			elif o == '-h': Usage()
			elif o == '-n': self.nt = 1
			elif o == '-s': self.sig = a
			elif o == '-t': self.tail = a
			elif o == '-w': self.w = "w"
		if args == ['-']: self.inp = sys.stdin.read()
		else: self.targets = args
		if self.inp or self.full:
			self.menu = '<Ctrl-C> to cancel or\n%s' % self.menu
			self.qfunc = '%s, <C-c>:cancel' % self.qfunc
			
	def interRuptus(self):
		if self.inp or self.full: sys.exit(0)
		else: self.sign = None

	def getString(self, fn):
		sigfile = os.path.join(self.sdir, fn)
		return readFile(sigfile)

	def getSig(self):
		siglist = filter(lambda f: f.endswith(self.tail),
				os.listdir(self.sdir) )
		if not siglist: return ''
		shuffle(siglist)
		self.items = [self.getString(fn) for fn in siglist]
		if self.pat and self.items:
			self.items = filter(lambda i: self.pat.search(i), self.items)
		try: self.sign = Tpager.interAct(self)
		except KeyboardInterrupt: self.interRuptus()

	def checkPattern(self):
		try: self.pat = re.compile(r'%s' % self.pat, re.IGNORECASE)
		except re.error, strerror:
			print 'Error in regular expression\n' \
			      '%s\n%s' % (self.pat, strerror)
			self.pat = None
			self.getPattern()

	def getPattern(self):
		if self.pat == None:
			try: self.pat = raw_input(self.menu)
			except KeyboardInterrupt: self.interRuptus()
		if self.sign != None: self.checkPattern()

	def siggiLoop(self):
		while 1:
			self.getSig()
			if self.sign and self.sign.startswith(self.ckey):
				self.pat = self.sign[1:]
				self.sign = ''
				self.checkPattern()
				Tpager.__init__(self,
					self.name, self.format, self.qfunc, self.ckey)
			else: break

	def underSign(self):
		if self.nt: LastExit.termInit(self)
		self.siggiLoop()
		if self.nt: LastExit.reInit(self)
		if self.sign is None and (self.inp or self.full):
			print self.inp[:-1]
		else:
			if not self.sign: self.sign = readFile(self.sig)
			if self.full: self.sign = '-- \n%s' % self.sign
			self.sign = self.sign.rstrip() # get rid of EOFnewline
			if not self.targets:
				if not self.inp: print self.sign
				else: print '%s%s' % (self.inp, self.sign)
			else:
				for targetfile in self.targets:
					writeFile(targetfile, self.sign, self.w)


def main():
	siggi = Signature()
	siggi.argParser()
	siggi.underSign()

if __name__ == '__main__': main()

# EOF vim:ft=python
