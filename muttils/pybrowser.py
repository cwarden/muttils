# $Id$

import ui, urlregex, util
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

def weburlregex():
    u = urlregex.urlregex(proto='web', uniq=False)
    u.urlobject(search=False)
    return u.url_re, u.proto_re


class browser(object):
    '''
    Visits items with default or given browser.
    '''
    def __init__(self, parentui=None, items=None, tb=False, xb=False):
        self.ui = parentui or ui.config()
        self.items = items
        self.tb = tb # text browser
        self.xb = xb # x11 browser
        self.conny = False # try to connect to net
        self.weburl_re, self.webproto_re = weburlregex()

    def urlcomplete(self, url):
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
            url = util.absolutepath(url)
            if not url.startswith('/'):
                url = os.path.join(os.getcwd, url)
            if not os.path.exists(url):
                raise util.DeadMan('%s: file not found' % url)
            url = 'file://%s' % url
        return url

    def urlvisit(self):
        '''Visit url(s).'''
        self.ui.updateconfig()
        xbrowser = self.ui.configitem('browser', 'xbrowser')
        textbrowser = self.ui.configitem('browser', 'textbrowser')
        self.items = (self.items
                or [self.ui.configitem('browser', 'homepage')])
        self.items = [self.urlcomplete(url) for url in self.items]
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
        except webbrowser.Error, inst:
            raise util.DeadMan(inst)
