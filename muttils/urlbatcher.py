# $Id$

###
# Caveat:
# If input is read from stdin, it should be of one type
# (text/plain, text/html, email) because the type detecting
# mechanism is only triggered once.
# However you should be able to run this on all kind of files,
# input is checked anew for each file.
###

import ui, util
from pybrowser import Browser, BrowserError
from kiosk import Kiosk, KioskError
from urlcollector import Urlcollector, UrlcollectorError
from iterm import iterm
import os

class UrlbatcherError(Exception):
    '''Exception class for the urlbatcher module.'''

class Urlbatcher(Browser, Urlcollector, Kiosk, iterm):
    '''
    Parses input for either web urls or message-ids.
    Browses all urls or creates a message tree in mutt.
    You can specify urls/ids by a regex pattern.
    '''
    defaults = {
            'proto': 'web',
            'files': None,
            'pat': None,
            'kiosk': '',
            'browse': False,
            'local': False,
            'mhiers': None,
            'mspool': True,
            'mask': None,
            'xb': False,
            'ftp': 'ftp',
            'getdir': '',
            }

    def __init__(self, opts={}):
        Browser.__init__(self)
        Urlcollector.__init__(self)
        Kiosk.__init__(self)
        iterm.__init__(self)
        for k in self.defaults.keys():
            setattr(self, k, opts.get(k, self.defaults[k]))

    def urlGo(self):
        if self.getdir:
            util.goonline()
            os.execvp('wget', ['wget', '-P', self.getdir] + self.items)
        else:
            try:
                self.urlVisit()
            except BrowserError, e:
                raise UrlbatcherError(e)
                    
    def urlSearch(self):
        if self.proto != 'mid':
            try:
                self.updateconfig()
                self.cpan = self.cfg.get('can', 'cpan')
                self.ctan = self.cfg.get('can', 'ctan')
            except ui.ConfigError, inst:
                raise UrlbatcherError(inst)
        try:
            self.urlCollect()
        except UrlcollectorError, e:
            raise UrlbatcherError(e)
        if not self.files:
            self.terminit()
        if self.items:
            yorn = '%s\nRetrieve the above %s? yes, [No] ' \
                    % ('\n'.join(self.items),
                       util.plural(len(self.items),
                           ('url', 'message-id')[self.proto=='mid']))
            if raw_input(yorn).lower() in ('y', 'yes'):
                if self.proto != 'mid':
                    self.urlGo()
                else:
                    try:
                        self.kioskStore()
                    except KioskError, e:
                        raise UrlbatcherError(e)
        else:
            msg = 'No %s found. [Ok] ' % ('url',
                    'message-id')[self.proto=='mid']
            raw_input(msg)
        if not self.files:
            self.reinit()
