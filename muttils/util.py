# $Id$

'''util.py - helper functions for muttils package
'''

import os, subprocess, sys

class DeadMan(Exception):
    '''Exception class for muttils package.'''
    def __init__(self, inst=''):
        self.inst = inst
    def __str__(self):
        if isinstance(self.inst, str):
            return self.inst
        return str(self.inst)

def updateattribs(obj, defaults, options):
    '''Updates default values with optional values.'''
    for k in defaults.iterkeys():
        if options.has_key(k):
            defaults[k] = options[k]
        setattr(obj, k, defaults[k])

def resolveopts(obj, defaults, options):
    '''Adapts option sets.
    Sets protocol to "web", if "getdir" or "ftpdir" is without
    corresponding protocol scheme.
    Sets protocol to "mid", if it encounters one of message_opts.'''

    webschemes = ['web', 'http', 'ftp']
    for o in ('getdir', 'ftpdir'):
        if (options.has_key(o) and options[o]
                and options.proto not in webschemes):
            options['proto'] = web
            break

    message_opts = ['midrelax', 'news', 'local', 'browse',
            'kiosk', 'mhiers', 'specdirs', 'mask']
    if options['proto'] != 'mid':
        for o in message_opts:
            if options[o]:
                options['proto'] = 'mid'
                options['decl'] = not options['midrelax']
                break
    else:
        options['decl'] = True
    del options['midrelax']

    updateattribs(obj, defaults, options)

def systemcall(cs, conny=False):
    '''Calls command sequence cs in manner suiting
    terminal connectivity.'''
    if conny:
        goonline()
    try:
        if os.isatty(sys.stdin.fileno()):
            # connected to terminal
            r = subprocess.call(cs)
        else:
            tty = os.ctermid()
            cs += ['<', tty, '>', tty]
            r = subprocess.call(' '.join(cs), shell=True)
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

def goonline():
    '''Connects Mac to internet, if conny is present.'''
    if os.uname()[0] == 'Darwin':
        try:
            import conny
            conny.appleconnect()
        except ImportError:
            pass
