class Tformat:
	"""
	Subclass to Pages (<- format, itemsdict, keys).
	Provides formatting methods
	for interactive terminal.
	"""
	def __init__(self, format='sf'):
		self.format = format
		self.itemsdict = {}  # dictionary of items to choose
		self.keys = []	     # itemsdict's keys
		self.maxl = 0 # length of last key
		# dictionary of format functions
		self.formdict = {'sf': self.simpleFormat,
			         'bf': self.bracketFormat}
	
	def formatItems(self):
		if not self.keys: return []
		if self.format == 'sf':
			self.maxl = len(self.keys[-1])
		formatfunc = self.formdict[self.format]
		return [formatfunc(key) for key in self.keys]

	def simpleFormat(self, key):
		"""Simple format of choice menu,
		recommended for 1 line items."""
		blank = ' ' * (self.maxl-len(key))
		return '%s%s) %s\n' \
			% (blank, key, self.itemsdict[key])
	
	def bracketFormat(self, key):
		"""Format of choice menu with items
		that are longer than 1 line."""
		return '[%s]\n%s\n' \
			% (key, self.itemsdict[key])
