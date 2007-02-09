# $Id$

'''util.py - helper functions for muttils package
'''

import os

def absolutepath(path):
    '''Guesses an absolute path, eg. given on command line.'''
    return os.path.normpath(os.path.abspath(os.path.expanduser(path)))

def plural(n, word):
    '''Returns "number word(s).'''
    return '%d %s%s' % (n, word, 's'[n==1:])

def goonline():
    '''Connects Mac to internet, if conny is present.'''
    if os.uname()[0] == 'Darwin':
        try:
            import conny
            conny.appleconnect()
        except ImportError:
            pass
