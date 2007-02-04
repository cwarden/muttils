# $Id$

import util
from urlregex.Urlregex import Urlregex
import os.path, re, socket, webbrowser

locals = socket.gethostbyaddr(socket.gethostname())
localaddresses = ['127.0.0.1']
for i in locals:
    if isinstance(i, str):
        i = [i]
    localaddresses += i
local_re = re.compile('http://(%s)' %
        '|'.join(re.escape(a) for a in localaddresses),
        re.IGNORECASE)
file_re  = re.compile(r'file:/+', re.IGNORECASE)

def webUrlRegex():
    u = Urlregex(proto='web', uniq=False)
    u.urlObjects(search=False)
    return u.url_re, u.proto_re


class BrowserError(Exception):
    '''Exception class for the pybrowser module.'''

class Browser(object):
    '''
    Visits items with default or given browser.
    '''
    def __init__(self, items=None, tb='', xb='', homeurl=''):
        self.items = items or [homeurl]
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
        self.items = [self.urlComplete(url) for url in self.items]
        try:
            if self.xb:
                b = webbrowser.get(self.xb)
            elif self.tb:
                b = webbrowser.get(self.tb)
            else:
                b = webbrowser
            if self.conny:
                util.goonline()
            for url in self.items:
                b.open(url)
        except webbrowser.Error, e:
            raise BrowserError(e)
