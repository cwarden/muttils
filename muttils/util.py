'''util.py - helper functions for muttils package
'''

# $Id$

import os, subprocess, sys

_notset = object()

def safehasattr(thing, attr):
    '''Deal with python compatibility problems of hasattr().
    See: http://selenic.com/hg/rev/5a0fdc715769'''
    return getattr(thing, attr, _notset) is not _notset


class DeadMan(Exception):
    '''Exception class for muttils package.
    '''
    def __init__(self, *args, **kw):
        Exception.__init__(self, *args)
        try:
            self.value = ' '.join(args)
        except TypeError:
            self.value = args
        self.hint = kw.get('hint')

    def __str__(self):
        if not self.value:
            return 'abort'
        if self.hint:
            self.value = '%s\n(%s)' % (self.value, self.hint)
        return 'abort: %s' % self.value


def version():
    try:
        from muttils import __version__
        return __version__.version
    except ImportError:
        return 'unknown'

def fullversion(proginfo):
    return ('%s (version %s)\n\n'
            'Copyright (C) 2007-2011 Christian Ebert <blacktrash@gmx.net>\n'
            'This is free software. See the source for copying conditions.\n'
            'The Muttils package comes with ABSOLUTELY NO WARRANTY.'
            % (proginfo, version()))

def termconnected():
    '''Returns true if we are connected to a terminal.'''
    try:
        return sys.stdin.isatty()
    except ValueError:
        # I/O operation on closed file
        return False

def cygwin():
    '''Returns true when we are on cygwin.'''
    return sys.platform == 'cygwin'

def systemcall(cs, notty=None, screen=None):
    '''Calls command sequence cs in manner suiting
    terminal connectivity.'''
    # programs that can be launched without terminal connection
    termprogs = 'w3m', 'wget'
    prog = cs[0]
    if notty is None:
        # check if connected to terminal
        notty = prog not in termprogs and not termconnected()
    if screen is None:
        # w3m behaves differently in screen
        screen = prog not in termprogs[1:] and 'STY' in os.environ
    try:
        if notty and not screen:
            tty = os.ctermid()
            cs += ['<', tty, '>', tty]
            r = subprocess.call(' '.join(cs), shell=True)
        else:
            if notty: # and screen
                cs = ['screen', '-X', 'screen'] + cs
            elif screen:
                cs.insert(0, 'screen')
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

def savedir(directory):
    '''Returns absolute path of directory if it is one.'''
    directory = absolutepath(directory)
    if not os.path.isdir(directory):
        raise DeadMan('%s: not a directory' % directory)
    return directory

def plural(n, word):
    '''Returns "number word(s)".'''
    return '%d %s%s' % (n, word, 's'[n==1:])
