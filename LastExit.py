# $Hg: LastExit.py,v$

import sys
from os import ctermid
from cheutils.readwrite import writeFile, readLine

class Termplus:
	"""
	Provides readline and write methods
	for an interactive terminal device.
	"""
	def __init__(self):
		self.dev = ctermid()

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
		stdin, stdout = Termplus(), Termplus()

	def reInit(self):
		"""Switches back to previous term."""
		sys.stdin, sys.stdout = self.iostack.pop()
