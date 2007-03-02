# $Id$

'''util.py - helper functions for muttils package
'''

import os, subprocess, sys

# programs that can be launched without terminal connection
term_progs = ('wget', 'w3m', 'osascript', 'ip-up')

class DeadMan(Exception):
    '''Exception class for muttils package.'''
    def __init__(self, inst=''):
        self.inst = inst
    def __str__(self):
        return '%s: abort: %s' % (os.path.basename(sys.argv[0]), self.inst)


def systemcall(cs, notty=False):
    '''Calls command sequence cs in manner suiting
    terminal connectivity.'''
    notty = (notty
            or os.path.basename(cs[0]) not in term_progs
            and not os.isatty(sys.stdin.fileno()))
    try:
        if notty: # not connected to terminal
            tty = os.ctermid()
            cs += ['<', tty, '>', tty]
            r = subprocess.call(' '.join(cs), shell=True)
        else:
            r = subprocess.call(cs)
        if r:
            raise DeadMan('%s returned %i' % (cs[0], r))
    except OSError, inst:
        raise DeadMan(inst)

def pipeline(cs):
    '''Returns first line of result of command sequence cs.'''
    p = subprocess.Popen(cs, close_fds=True,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    return p.stdout.readline()

def absolutepath(path):
    '''Guesses an absolute path, eg. given on command line.'''
    return os.path.normpath(os.path.abspath(os.path.expanduser(path)))

def plural(n, word):
    '''Returns "number word(s).'''
    return '%d %s%s' % (n, word, 's'[n==1:])
