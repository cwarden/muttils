# $Id$

import os, subprocess

'''
Provides number of rows and columns
of current terminal.
'''

if os.uname()[0] == 'Darwin':
    tt = subprocess.Popen(['stty', '-f', os.ctermid(), '-a'],
            stdout=subprocess.PIPE).communicate()[0]
    attribs = tt.split()
    t_rows = int(attribs[3])
    t_cols = int(attribs[5])
else: # Linux
    tt = subprocess.Popen(['stty', '-F', os.ctermid(), '-a'],
            stdout=subprocess.PIPE).communicate()[0]
    attribs = tt.split('; ')
    t_rows = int(attribs[1].split()[1])
    t_cols = int(attribs[2].split()[1])

def _test():
    print 'This terminal has %d rows and %d columns.' % (t_rows, t_cols)
