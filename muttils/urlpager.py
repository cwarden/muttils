# $Id$

import ui, util
from pybrowser import Browser, BrowserError
from urlregex.Urlcollector import Urlcollector, UrlcollectorError
from urlregex.kiosk import Kiosk, KioskError
from tpager.Tpager import Tpager, TpagerError
from urlregex.Urlregex import mailCheck, ftpCheck
import os, readline

class UrlpagerError(Exception):
    '''Exception class for the urlpager module.'''

class Urlpager(Urlcollector, Tpager, Browser, Kiosk):

    defaults = {
            'proto': 'all',
            'files': None,
            'pat': None,
            'kiosk': '',
            'browse': False,
            'local': False,
            'mhiers': None,
            'mspool': True,
            'mask': None,
            'xb': False,
            'tb': False,
            'ftp': 'ftp',
            'getdir': '',
            }

    def __init__(self, opts={}):
        Browser.__init__(self)
        Urlcollector.__init__(self)
        Tpager.__init__(self, name='url')
        Kiosk.__init__(self)

        for k in self.defaults.keys():
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
            try:
                self.updateconfig('messages')
            except ui.ConfigError, inst:
                raise UrlpagerError(inst)
            cs = [self.cfg.get('messages', 'mailer')]
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
            cs += [url]
            if conny:
                util.goonline()
            elif not self.files: # mail client needs terminal
                tty = os.ctermid()
                cs += ['<', tty, '>', tty]
                os.system(' '.join(cs))
            else:
                os.execvp(cs[0], cs)

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
