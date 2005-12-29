# $Id: terminfo.py,v 1.3 2005/12/29 16:50:25 chris Exp $

import os

"""
Provides number of rows and columns
of current terminal.
"""

osname = os.uname()[0]
if osname == 'Darwin':
	dev = os.ctermid()
	tt = os.popen('stty -f %s -a' % dev)
	attribs = tt.readline().split()
	t_rows = int(attribs[3])
	t_cols = int(attribs[5])
elif osname == 'Linux':
	tt = os.popen('stty -F /dev/tty -a')
	attribs = tt.readline().split('; ')
	t_rows = int(attribs[1].split()[1])
	t_cols = int(attribs[2].split()[1])

def _test():
	print 'This terminal has %d rows and %d columns.' \
		% (t_rows, t_cols)
