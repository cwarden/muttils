# $Hg: Tpager.py,v$

from Pages import Pages
from cheutils.spl import sPl
from cheutils.valclamp import valClamp

# format default paging command
pds = {-1:"Back", 1:"Forward"}

class TpagerError(Exception):
	"""Exception class for Tpager."""

class Tpager(Pages):
	"""
	Customizes interactive choice to current terminal.
	"""
	def __init__(self, name="item", format="sf",
			qfunc="Quit", ckey="", crit="pattern"):
		Pages.__init__(self) 	   # <- items, ilen, pages, itemsdict, cols
		self.name = name           # general name of an item
		if format in ("sf", "bf"): # available formats
			self.format = format # key to format function
		else:
			e = "the `%s' format is invalid." % format
			raise TpagerError, e
		self.qfunc = qfunc         # name of exit function
		if ckey and ckey in "qQ-":
			e = "the `%s' key is internally reserved." % ckey
			raise TpagerError, e
		else:
			self.ckey = ckey   # key to customize pager
		self.crit = crit           # criterion for customizing
		self.mcols = self.cols - 3 # available columms for menu
		self.header = ""

	def colTrunc(self, s, cols=0):
		"""Truncates string at beginning by inserting ">"
		if the string's width exceeds cols."""
		if not cols:
			cols = self.mcols
		slen = len(s)
		if slen <= cols:
			return s
		else:
			return ">%s" % s[slen-cols:]

	def pageDisplay(self, menu, pn=1):
		"""Displays a page of items including header and choice menu."""
		print self.header + self.pages[pn]
		return raw_input(self.colTrunc(menu))

	def interAct(self, newdict=True):
		"""Lets user page through a list of items and make a choice."""
		if newdict: Pages.pagesDict(self)
		self.header = "*%s*" % sPl(self.ilen, self.name)
		self.header = "%s\n\n" % self.colTrunc(self.header, self.cols-2)
		plen = len(self.pages)
		if plen == 1: # no paging
			cs = ""
			if self.ckey:
				cs = ", %s<%s>" % (self.ckey, self.crit)
			if self.itemsdict:
				cs = "%s, number" % cs
			menu = "Page 1 of 1 [%s]%s " % (self.qfunc, cs)
			reply = self.pageDisplay(menu)
			if not reply:
				return 0
			elif reply in self.itemsdict:
				return self.itemsdict[reply]
			elif self.ckey and reply.startswith(self.ckey):
				return reply
			else: self.interAct(newdict=False) # display same page
		else: # more than 1 page
			pn = 1 # start at first page
			pdir = -1 # initial paging direction reversed
			while 1:
				bs = "" # reverse paging direction
				if 1 < pn < plen:
					bs = "-:%s, " % pds[pdir*-1]
				else:
					pdir *= -1
				menu = "Page %d of %d [%s], %sq:%s" \
					% (pn, plen, pds[pdir], bs, self.qfunc)
				if self.ckey:
					menu = "%s, %s<%s>" % (menu, self.ckey, self.crit)
				menu = "%s, number " % menu
				reply = self.pageDisplay(menu, pn)
				if reply:
					if reply in "qQ":
						return 0
					elif reply in self.itemsdict:
						return self.itemsdict[reply]
					elif self.ckey and reply.startswith(self.ckey):
						return reply
					elif reply == "-" and bs:
						pdir *= -1
						pn = valClamp(pn+pdir, 1, plen)
					#else: same page displayed on invalid response
				else:
					pn = valClamp(pn+pdir, 1, plen)
