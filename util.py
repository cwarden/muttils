# $Id$

'''util.py - helper functions for urlregex package
'''

import os.path

def absolutepath(path):
    '''Guesses an absolute path, eg. given on command line.'''
    return os.path.normpath(os.path.abspath(os.path.expanduser(path)))

def goonline():
    '''Connects Mac to internet, if cheutils.conny is present.'''
    try:
        from cheutils import conny
        conny.appleConnect()
    except ImportError:
        pass
