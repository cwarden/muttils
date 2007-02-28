# $Id$

'''util.py - helper functions for muttils package
'''

import os, subprocess, sys

web_schemes = ('web', 'http', 'ftp')
message_opts = ('midrelax', 'news', 'local', 'browse',
        'kiosk', 'mhiers', 'specdirs', 'mask')
# programs that can be launched without terminal connection
term_progs = ('wget', 'w3m', 'osascript', 'ip-up')

class DeadMan(Exception):
    '''Exception class for muttils package.'''
    def __init__(self, inst=''):
        self.inst = inst
    def __str__(self):
        return '%s: abort: %s' % (os.path.basename(sys.argv[0]), self.inst)


def updateattribs(obj, options):
    '''Updates default values with optional values.'''
    for k in obj.defaults.iterkeys():
        if options.has_key(k):
            obj.defaults[k] = options[k]
        setattr(obj, k, obj.defaults[k])

def resolveopts(obj, options):
    '''Adapts option sets.
    Sets protocol to "web", if "getdir" or "ftpdir" is without
    corresponding protocol scheme.
    Sets protocol to "mid", if it encounters one of message_opts.'''
    for o in ('getdir', 'ftpdir'):
        if (options.has_key(o) and options[o]
                and options['proto'] not in web_schemes):
            options['proto'] = 'web'
            break
    if options['proto'] != 'mid':
        for o in message_opts:
            if options[o]:
                options['proto'] = 'mid'
                options['decl'] = not options['midrelax']
                break
    else:
        options['decl'] = True
    del options['midrelax']
    updateattribs(obj, options)

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

def absolutepath(path):
    '''Guesses an absolute path, eg. given on command line.'''
    return os.path.normpath(os.path.abspath(os.path.expanduser(path)))

def plural(n, word):
    '''Returns "number word(s).'''
    return '%d %s%s' % (n, word, 's'[n==1:])
