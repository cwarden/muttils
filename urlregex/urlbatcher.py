# $Id$

###
# Caveat:
# If input is read from stdin, it should be of one type
# (text/plain, text/html, email) because the type detecting
# mechanism is only triggered once.
# However you should be able to run this on all kind of files,
# input is checked anew for each file.
###

import urlregex.util
from urlregex.Urlcollector import Urlcollector, UrlcollectorError
from urlregex.kiosk import Kiosk, KioskError
from tpager.LastExit import LastExit
from cheutils.selbrowser import Browser, BrowserError

class UrlbatcherError(Exception):
    '''Exception class for the urlbatcher module.'''

class Urlbatcher(Browser, Urlcollector, Kiosk, LastExit):
    '''
    Parses input for either web urls or message-ids.
    Browses all urls or creates a message tree in mutt.
    You can specify urls/ids by a regex pattern.
    '''
    defaults = {
            'proto': 'web',
            'files': [],
            'pat': None,
            'kiosk': '',
            'browse': False,
            'local': False,
            'mhiers': [],
            'mspool': True,
            'mask': None,
            'xb': '',
            'ftp': 'ftp',
            'getdir': '',
            'mailer': 'mail',
            }

    def __init__(self, opts={}):
        Urlcollector.__init__(self)
        Browser.__init__(self)
        Kiosk.__init__(self)
        LastExit.__init__(self)
        for k in self.defaults.keys():
            setattr(self, k, opts.get(k, self.defaults[k]))

    def urlGo(self):
        if self.getdir:
            os.system('wget -P %s %s' % (self.getdir, ' '.join.self.items))
        else:
            try:
                self.urlVisit()
            except BrowserError, e:
                raise UrlbatcherError(e)
                    
    def urlSearch(self):
        try:
            self.urlCollect()
        except UrlcollectorError, e:
            raise UrlbatcherError(e)
        if not self.files:
            self.termInit()
        if self.items:
            yorn = '%s\nRetrieve the above %s? yes, [No] ' \
                    % ('\n'.join(self.items),
                       urlregex.util.plural(len(self.items),
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
            self.reInit()
