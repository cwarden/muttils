# $Id$

'''util.py - helper functions for muttils package
'''

import os

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
    Sets protocol to "web", if "getdir" is without corresponding proto.
    Sets protocol to "mid", if it encounters one of message_opts.'''

    webschemes = ['web', 'http', 'ftp']
    if options['getdir'] and options['proto'] not in webschemes:
        options['proto'] = 'web'

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
