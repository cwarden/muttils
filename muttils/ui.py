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
                }
        self.cfg = ConfigParser.SafeConfigParser(defaults)

    def updateconfig(self, *sections):
        sections = sections or self.cfg.defaults().keys()
        try:
            self.cfg.read(self.rcpath)
        except ConfigParser.ParsingError, inst:
            raise ConfigError(inst)
        for section in sections:
            if not self.cfg.has_section(section):
                self.cfg.add_section(section)
            for name, value in self.cfg.defaults()[section]:
                if not self.cfg.has_option(section, name):
                    self.cfg.set(section, name, value)
