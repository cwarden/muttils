# $Id$

'''ui.py - user interface for muttils package
'''

import util
import ConfigParser, os.path, sys

default_rcpath = ['/etc/muttils/muttilsrc',
                  '/usr/local/etc/muttilsrc',
                  os.path.expanduser('~/.muttilsrc'),]

default_config = {'messages': [('mailer', 'mutt'),
                               ('maildirs', ''),
                               ('signature', ''),
                               ('sigdir', ''),
                               ('sigtail', ''),],
                  'net': [('connect', ''),
                          ('homepage', ''),
                          ('ftpclient', 'ftp'),
                          ('cpan', 'ftp://ftp.cpan.org/pub/CPAN'),
                          ('ctan', 'ftp://ftp.ctan.org/tex-archive'),],}

web_schemes = ('web', 'http', 'ftp')
message_opts = ('midrelax', 'news', 'local', 'browse',
                'kiosk', 'mhiers', 'specdirs', 'mask')

class ui(object):
    def __init__(self, rcpath=None):
        self.rcpath = rcpath or default_rcpath
        self.config = ConfigParser.SafeConfigParser(default_config)
        self.updated = False # is config already up to date?
        # ui attributes that are governed by options
        self.proto = 'all'   # url protocol scheme
        self.decl = False    # only care about urls prefixed with scheme
        self.pat = None      # pattern to match urls against
        self.kiosk = ''      # path to mbox to append retrieved messages
        self.browse = False  # browse Google for messages?
        self.local = False   # search messages only locally?
        self.news = False    # search local mailboxes?
        self.mhiers = ''     # colon separated list of mail hierarchies
        self.specdirs = ''   # colon separated list of specified mail hierarchies
        self.mask = None     # file mask for mail hierarchies
        self.app = ''        # browser program
        self.ftpdir = ''     # download directory for ftp
        self.getdir = ''     # download directory for wget

    def updateconfig(self):
        if self.updated:
            return
        defaults = self.config.defaults()
        sections = defaults.keys()
        try:
            self.config.read(self.rcpath)
        except ConfigParser.ParsingError, inst:
            raise util.DeadMan(inst)
        for section in sections:
            if not self.config.has_section(section):
                self.config.add_section(section)
            for name, value in defaults[section]:
                if not self.config.has_option(section, name):
                    self.config.set(section, name, value)
        self.updated = True

    def configitem(self, section, name):
        '''Returns value of name of section of config.'''
        return self.config.get(section, name)

    def resolveopts(self, options):
        '''Adapts option sets.
        Sets protocol to "web", if "getdir" is without corresponding
        protocol scheme.
        Sets protocol to "mid", if it encounters one of message_opts.
        And, finally, update ui's attributes with current options.'''
        if (options.has_key('getdir') and options['getdir']
                and options['proto'] not in web_schemes):
            options['proto'] = 'web'
        if options['proto'] != 'mid':
            for o in message_opts:
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
        if not sys.stdout.closed:
            sys.stdout.flush()
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
