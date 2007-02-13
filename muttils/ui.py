# $Id$

'''ui.py - user interface for muttils package
'''

import util
import ConfigParser, os.path

class config(object):
    def __init__(self, rcpath=None):
        self.rcpath = rcpath or [
                '/etc/muttilsrc',
                '/usr/local/etc/muttilsrc',
                os.path.expanduser('~/.muttilsrc')]
        defaults = {
                'messages':
                [('mailer', 'mail'), ('maildirs', None)],
                'browser':
                [('textbrowser', ''), ('xbrowser', ''), ('homepage', '')],
                'can':
                [('cpan', 'ftp://ftp.cpan.org/pub/CPAN'),
                    ('ctan', 'ftp://ftp.ctan.org/tex-archive')],
                }
        self.config = ConfigParser.SafeConfigParser(defaults)
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
