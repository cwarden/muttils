# $Id$

'''ui.py - user interface for muttils package
'''

import ConfigParser, os.path, sys
from muttils import util

class ui(object):
    config = None
    updated = False # is config already up to date?
    # ui attributes that are governed by options
    proto = 'all'   # url protocol scheme
    decl = False    # only care about urls prefixed with scheme
    pat = None      # pattern to match urls against
    kiosk = ''      # path to mbox to append retrieved messages
    browse = False  # browse Google for messages?
    local = False   # search messages only locally?
    news = False    # search local mailboxes?
    mhiers = ''     # colon separated list of mail hierarchies
    specdirs = ''   # colon separated list of specified mail hierarchies
    mask = None     # file mask for mail hierarchies
    app = ''        # browser program
    ftpdir = ''     # download directory for ftp
    getdir = ''     # download directory for wget

    defrcpath = ['/etc/muttils/muttilsrc',
                 '/usr/local/etc/muttilsrc',
                 os.path.expanduser('~/.muttilsrc'),]

    def __init__(self, rcpath=None):
        self.rcpath = rcpath or self.defrcpath
        self.config = ConfigParser.SafeConfigParser()

    def updateconfig(self):
        if self.updated:
            return
        try:
            self.config.read(self.rcpath)
        except ConfigParser.ParsingError, inst:
            raise util.DeadMan(inst)
        self.updated = True

    def configitem(self, section, name, default=None):
        '''Returns value of name of section of config.'''
        if self.config.has_option(section, name):
            return self.config.get(section, name)
        return default

    def configbool(self, section, name, default=False):
        '''Returns boolean value of name of section of config.'''
        if self.config.has_option(section, name):
            return self.config.getboolean(section, name)
        return default

    def configlist(self, section, name, default=None):
        '''Returns value of name of section of config as list.'''
        cfg = self.configitem(section, name)
        if cfg is None:
            return default or []
        if isinstance(cfg, basestring):
            return cfg.replace(',', ' ').split()
        return cfg

    def configint(self, section, name, default=0):
        cfg = self.configitem(section, name)
        if cfg is None:
            return default
        try:
            return int(cfg)
        except ValueError, inst:
            raise util.DeadMan(inst)

    def resolveopts(self, options):
        '''Adapts option sets.
        Sets protocol to "web", if "getdir" is without corresponding
        protocol scheme.
        Sets protocol to "mid", if it encounters one of messageopts.
        And, finally, update ui's attributes with current options.'''
        webschemes = ('web', 'http', 'ftp')
        messageopts = ('midrelax', 'news', 'local', 'browse',
                       'kiosk', 'mhiers', 'specdirs', 'mask')
        if options.get('getdir', '') and options['proto'] not in webschemes:
            options['proto'] = 'web'
        if options['proto'] != 'mid':
            for o in messageopts:
                if options[o]:
                    options['proto'] = 'mid'
                    options['decl'] = not options['midrelax']
                    break
        else:
            options['decl'] = True
        del options['midrelax']
        try:
            for o in options.iterkeys():
                setattr(self, o, options[o])
        except KeyError:
            raise util.DeadMan('%s: invalid option' % o)

    def write(self, *args):
        for a in args:
            sys.stdout.write(str(a))

    def note(self, *msg):
        self.write(*msg)

    def warn(self, *args):
        try:
            if not sys.stdout.closed:
                sys.stdout.flush()
        except AttributeError:
            pass
        sys.stderr.write('%s: ' % os.path.basename(sys.argv[0]))
        sys.stderr.flush()
        for a in args:
            sys.stderr.write(str(a))

    def flush(self):
        try:
            sys.stdout.flush()
        except:
            pass
        try:
            sys.stderr.flush()
        except:
            pass
