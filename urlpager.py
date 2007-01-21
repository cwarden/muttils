# $Id$

import os, readline
from Urlcollector import Urlcollector, UrlcollectorError
from tpager.Tpager import Tpager, TpagerError
from cheutils.selbrowser import Browser, BrowserError
from kiosk import Kiosk, KioskError
from Urlregex import mailCheck, ftpCheck
from cheutils import systemcall

def goOnline():
    try:
        from cheutils import conny
        conny.appleConnect()
    except ImportError:
        pass

class UrlpagerError(Exception):
    '''Exception class for the urlpager module.'''

class Urlpager(Urlcollector, Tpager, Browser, Kiosk):

    defaults = {
            'proto': 'all',
            'files': [],
            'pat': None,
            'kiosk': '',
            'browse': False,
            'local': False,
            'mhiers': [],
            'mspool': True,
            'mask': None,
            'xb': '',
            'tb': '',
            'ftp': 'ftp',
            'getdir': '',
            'mailer': 'mail',
            }

    def __init__(self, opts={}):
        Urlcollector.__init__(self)
        Tpager.__init__(self, name='url')
        Browser.__init__(self)
        Kiosk.__init__(self)

        for k in self.defaults:
            setattr(self, k, opts.get(k, self.defaults[k]))

    def urlPager(self):
        if self.proto not in ('all', 'mid'):
            self.name = '%s %s' % (self.proto, self.name)
        elif self.proto == 'mid':
            self.name = 'message-id'
        self.name = 'unique %s' % self.name
        try:
            # as there is no ckey, interAct() returns always 0
            self.interAct()
        except TpagerError, e:
            raise UrlpagerError(e)

    def urlGo(self):
        url, cs, conny = self.items[0], [], True
        if (self.proto == 'mailto'
                or self.proto == 'all' and mailCheck(url)):
            cs = [self.mailer]
            conny = False
        elif self.getdir:
            cs = ['wget', '-P', self.getdir]
        elif self.proto == 'ftp' or ftpCheck(url):
            if not os.path.splitext(url)[1] and not url.endswith('/'):
                self.items = [url + '/']
            cs = [self.ftp]
        if not cs:
            try:
                self.urlVisit()
            except BrowserError, e:
                raise UrlpagerError(e)
        else:
            if conny:
                goOnline()
            cs += self.items
            if not self.getdir and not self.files: # program needs terminal
                tty = os.ctermid()
                cs += ['<', tty, '>', tty]
                cs = ' '.join(cs)
                systemcall.systemCall(cs, sh=True)
            else:
                systemcall.systemCall(cs)

    def urlSearch(self):
        try:
            self.urlCollect()
        except UrlcollectorError, e:
            raise UrlpagerError(e)
        self.urlPager()
        if not self.items:
            return
        if self.proto != 'mid':
            try:
                if self.files:
                    readline.add_history(self.items[0])
                    url = raw_input('\n\npress <UP> or <C-P> to edit url, '
                            '<C-C> to cancel or <RET> to accept\n%s\n'
                            % self.items[0])
                else:
                    self.termInit()
                    url = raw_input('\n\npress <RET> to accept or <C-C> to cancel, '
                            'or enter url manually\n%s\n' % self.items[0])
                    self.reInit()
                if url:
                    self.items = [url]
                self.urlGo()
            except KeyboardInterrupt:
                pass
        else:
            try:
                self.kioskStore()
            except KioskError, e:
                raise UrlpagerError(e)
