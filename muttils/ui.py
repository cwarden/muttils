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
                'mailer': 'mail',
                'maildirs': None,
                'textbrowser': '',
                'xbrowser': '',
                'homepage': '',
                }
        self.rcdata = ConfigParser.SafeConfigParser(defaults)
        try:
            self.rcdata.read(self.rcpath)
        except ConfigParser.ParsingError, inst:
            raise ConfigError(inst)

    def get(self, section, option):
        if (self.rcdata.has_section(section)
                and self.rcdata.has_option(section, option)):
            return self.rcdata.get(section, option)
        return self.rcdata.defaults()[option]
