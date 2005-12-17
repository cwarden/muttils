# $Id: LastExit.py,v 1.4 2005/12/17 15:54:56 chris Exp $

import os, sys
from cheutils.readwrite import writeFile, readLine

class Termplus:
	"""
	Provides readline and write methods
	for an interactive terminal device.
	"""
	def __init__(self):
		self.dev = os.ctermid()

	def write(self, o):
		writeFile(self.dev, o)
	
	def readline(self, size=-1):
		return readLine(self.dev, size=size)


class LastExit(Termplus):
	"""
	Provides interactive terminal devices.
	"""
	def __init__(self):
		self.iostack = []

	def termInit(self):
		self.iostack.append((sys.stdin, sys.stdout))
		sys.stdin, sys.stdout = Termplus(), Termplus()

	def reInit(self):
		"""Switches back to previous term."""
		sys.stdin, sys.stdout = self.iostack.pop()

# EOF vim:ft=python
