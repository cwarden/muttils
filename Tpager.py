from Pages import Pages
from spl import sPl
from valclamp import valClamp

# format default paging command
pds = {-1:'Back', 1:'Forward'}

class Tpager(Pages):
	"""
	Useful for interactive choice in a terminal window.
	"""
	def __init__(self, name='item', format='sf', qfunc='Quit', ckey='', crit='pattern'):
		Pages.__init__(self) # <- items, ilen, pages, itemsdict, cols
		self.name = name     # general name of an item
		self.format = format # key to format function
		self.qfunc = qfunc   # name of exit function
		self.ckey = ckey     # key to customize pager
		self.crit = crit     # criterion for customizing

	def checkReply(self, reply, prompt):
		if reply in self.itemsdict:
			return self.itemsdict[reply]
		elif reply.startswith(self.ckey):
			return reply
		return 0
		# to do: react to invalid answer

	def interAct(self):
		Pages.pagesDict(self)
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
			return self.checkReply(reply)
		# more than 1 page
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
			if reply and reply != 'b':
				return self.checkReply(reply)
			if reply and bs:
				pdir *= -1
			pn = valClamp(pn+pdir, 1, plen)
