# $Id$

'''ui.py - user interface for muttils package
'''

import ConfigParser, os.path

class ConfigError(Exception):
    '''Exception class for configuration.'''

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
        self.cfg = ConfigParser.SafeConfigParser(defaults)
        self.updated = False

    def updateconfig(self):
        if self.updated:
            return
        defaults = self.cfg.defaults()
        sections = defaults.keys()
        try:
            self.cfg.read(self.rcpath)
        except ConfigParser.ParsingError, inst:
            raise ConfigError(inst)
        for section in sections:
            if not self.cfg.has_section(section):
                self.cfg.add_section(section)
            for name, value in defaults[section]:
                if not self.cfg.has_option(section, name):
                    self.cfg.set(section, name, value)
        self.updated = True
