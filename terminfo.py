# $Hg: terminfo.py,v$

import os
from cheutils import systemcall

'''
Provides number of rows and columns
of current terminal.
'''

osname = os.uname()[0]
dev = os.ctermid()
if osname == 'Darwin':
    tt = systemcall.backQuote(['stty', '-f', dev, '-a'])
    attribs = tt.split()
    t_rows = int(attribs[3])
    t_cols = int(attribs[5])
elif osname == 'Linux':
    tt = systemcall.backQuote(['stty', '-F', dev, '-a'])
    attribs = tt.split('; ')
    t_rows = int(attribs[1].split()[1])
    t_cols = int(attribs[2].split()[1])

def _test():
    print 'This terminal has %d rows and %d columns.' % (t_rows, t_cols)
