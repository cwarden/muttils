from Pages import Pages
from spl import sPl
from valclamp import valClamp

# format default paging command
pds = {-1:'Back', 1:'Forward'}

def codeError(msg):
	import sys
	print 'Tpager.py: %s\nCheck %s code!' % (msg, sys.argv[0])
	sys.exit(2)

class Tpager(Pages):
	"""
	Useful for interactive choice in a terminal window.
	"""
	def __init__(self, name='item', format='sf', qfunc='Quit', ckey='', crit='pattern'):
		Pages.__init__(self) # <- items, ilen, pages, itemsdict, cols
		self.name = name     # general name of an item
		if format in ('sf', 'bf'): # available formats
			self.format = format # key to format function
		else:
			msg = 'the "%s" format is invalid.' % format
			codeError(msg)
		self.qfunc = qfunc   # name of exit function
		if ckey and ckey in 'qQbB':
			msg = 'the "%s" key is internally reserved.' % ckey
			codeError(msg)
		else:
			self.ckey = ckey     # key to customize pager
		self.crit = crit     # criterion for customizing

	def interAct(self, newdict=True):
		if newdict: Pages.pagesDict(self)
		mcols = self.cols - 3 # available columms for menu
		hcols = self.cols - 2 # available columms for headline
		headline = '*%s*' % sPl(self.ilen, self.name)
		hlen = len(headline)
		if hlen > hcols: # headline exceeds columns
			headline = '>%s' % headline[hlen-hcols:]
		header = '%s\n\n' % headline
		plen = len(self.pages)
		if plen == 1: # no paging
			print header + self.pages[1]
			cs = ''
			if self.ckey: cs = ', %s<%s>' % (self.ckey, self.crit)
			if self.itemsdict: cs = '%s, number' % cs
			prompt = 'Page 1 of 1 ([%s]%s) ' \
				% (self.qfunc, cs)
			mlen = len(prompt)
			if mlen > self.cols: # menu exceeds columns
				prompt = '>%s' % prompt[mlen-mcols:]
			reply = raw_input(prompt)
#                        return self.checkReply(reply)
			if not reply: return 0
			elif reply in self.itemsdict:
				return self.itemsdict[reply]
			elif self.ckey and reply.startswith(self.ckey):
				return reply
			else: self.interAct(newdict=False)
		else:# more than 1 page
			pn = 1 # start at 1. page
			pdir = -1 # initial paging direction reversed
			while 1:
				bs = '' # reverse paging direction
				print header + self.pages[pn]
				if pn in (1, plen):
					pdir *= -1
				if 1 < pn < plen:
					bs = 'b:%s, ' % pds[pdir*-1]
				menu = 'Page %d of %d ([%s], %sq:%s' \
					% (pn, plen, pds[pdir], bs, self.qfunc)
				if self.ckey: menu = '%s, %s<%s>' % (menu, self.ckey, self.crit)
				menu = '%s, number) ' % menu
				mlen = len(menu)
				if mlen > self.cols: # menu has too many columns
					menu = '>%s' % menu[mlen-mcols:]
				reply = raw_input(menu)
				if reply:
					if reply in 'qQ': return 0
					elif reply in self.itemsdict:
						return self.itemsdict[reply]
					elif self.ckey and reply.startswith(self.ckey):
						return reply
					elif reply in 'bB' and bs:
						pdir *= -1
						pn = valClamp(pn+pdir, 1, plen)
					# nothing happens on invalid response
				else: pn = valClamp(pn+pdir, 1, plen)
