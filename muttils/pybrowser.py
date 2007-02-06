# $Id$

import ui, util
from urlregex.Urlregex import Urlregex
import os.path, re, socket, webbrowser

def getlocals():
    '''Returns valid local addresses.'''
    l = socket.gethostbyaddr(socket.gethostname())
    localaddresses = ['127.0.0.1']
    for i in l:
        if isinstance(i, str):
            i = [i]
        localaddresses += i
    return localaddresses

local_re = re.compile('http://(%s)' %
        '|'.join(re.escape(a) for a in getlocals()),
        re.IGNORECASE)
file_re  = re.compile(r'file:/+', re.IGNORECASE)

def webUrlRegex():
    u = Urlregex(proto='web', uniq=False)
    u.urlObjects(search=False)
    return u.url_re, u.proto_re


class BrowserError(Exception):
    '''Exception class for the pybrowser module.'''

class Browser(ui.config):
    '''
    Visits items with default or given browser.
    '''
    def __init__(self, items=None, tb=False, xb=False):
        ui.config.__init__(self)
        self.items = items
        self.tb = tb # text browser
        self.xb = xb # x11 browser
        self.conny = False # try to connect to net
        self.weburl_re, self.webproto_re = webUrlRegex()

    def urlComplete(self, url):
        '''Adapts possibly short url to pass as browser argument.'''
        if self.weburl_re.match(url):
            # not local
            self.conny = True
            if self.webproto_re and not self.webproto_re.match(url):
                # eg. tug.org -> http://tug.org
                url = 'http://%s' % url
        elif not local_re.match(url):
            # strip url to pure pathname
            url = file_re.sub('/', url, 1)
            if not os.path.exists(util.absolutepath(url)):
                raise BrowserError('%s: file not found')
            url = 'file://%s' % url
        return url

    def urlVisit(self):
        '''Visit url(s).'''
        try:
            self.updateconfig()
        except ui.ConfigError, inst:
            raise BrowserError(inst)
        xbrowser = self.cfg.get('browser', 'xbrowser')
        textbrowser = self.cfg.get('browser', 'textbrowser')
        self.items = self.items or [self.cfg.get('browser', 'homepage')]

        self.items = [self.urlComplete(url) for url in self.items]
        try:
            if self.xb and xbrowser:
                b = webbrowser.get(xbrowser)
            elif self.tb and textbrowser:
                b = webbrowser.get(textbrowser)
            else:
                b = webbrowser
            if self.conny:
                util.goonline()
            for url in self.items:
                b.open(url)
        except webbrowser.Error, e:
            raise BrowserError(e)
