# $Id$

'''ui.py - user interface for muttils package
'''

import util
import ConfigParser, os.path, sys

default_rcpath = [
        '/etc/muttils/muttilsrc',
        '/usr/local/etc/muttilsrc',
        os.path.expanduser('~/.muttilsrc'),
        ]

default_config = {
        'messages': [
            ('mailer', 'mail'),
            ('maildirs', None),
            ('signature', ''),
            ('sigdir', ''),
            ('sigtail', ''),
            ],
        'net': [
            ('connect', ''),
            ('homepage', ''),
            ('ftpclient', 'ftp'),
            ('cpan', 'ftp://ftp.cpan.org/pub/CPAN'),
            ('ctan', 'ftp://ftp.ctan.org/tex-archive'),
            ],
        }

class ui(object):
    def __init__(self, rcpath=None):
        self.rcpath = rcpath or default_rcpath
        self.config = ConfigParser.SafeConfigParser(default_config)
        self.updated = False

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
