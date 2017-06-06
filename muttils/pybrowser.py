# $Id$

import os, webbrowser
from muttils import ui, urlregex, util

class PybrowserError(util.DeadMan):
    '''
    Error class for the pybrowser module.
    '''
    def __init__(self, *args, **kw):
        util.DeadMan.__init__(self, *args, **kw)
        if not self.value:
            self.value = 'could not locate runnable browser'

class browser(object):
    '''
    Visits items with default or given browser.
    '''
    weburl_re = None          # url protocol scheme regex
    appname = ''

    def __init__(self, parentui=None, items=None, app=None, evalurl=False):
        self.ui = parentui or ui.ui()
        self.ui.updateconfig()
        self.items = items             # urls
        if app is not None:
            self.ui.app = app
        try:
            self.ui.app = webbrowser.get(self.ui.app)
        except webbrowser.Error, inst:
            raise PybrowserError(inst)
        try:
            # lynx.old -> lynx, lynx.exe -> lynx
            self.appname = os.path.splitext(self.ui.app.basename)[0]
        except AttributeError:
            pass
        if evalurl: # check remote url protocol scheme
            self.ui.proto = 'web'
            u = urlregex.urlregex(self.ui, uniq=False)
            u.urlobject(search=False)
            self.weburl_re = u.url_re

    def fixurl(self, url, cygpath):
        '''Adapts possibly short url to pass as browser argument.'''
        if not self.weburl_re or self.weburl_re.match(url):
            url = urlregex.webschemecomplete(url)
            gophers = 'lynx', 'firefox'
            if url.startswith('gopher://') and self.appname not in gophers:
                # use gateway when browser is not gopher capable
                url = url.replace('gopher://',
                                  'http://gopher.floodgap.com/gopher/gw?')
        else: # local
            if url.startswith('file:'):
                # drop scheme in favour of local path
                # as some browsers do not handle file scheme gracefully
                url = url[5:]
                if url.startswith('//'):
                    url = url[2:]
                    if not url.startswith('/'):
                        # drop host part (validity of path checked below)
                        url = '/' + url.split('/', 1)[1]
            if not url.startswith('https://') and not url.startswith('http://'):
                url = util.absolutepath(url)
                if not os.path.exists(url):
                    raise PybrowserError('%s: not found' % url)
                if cygpath:
                    url = util.pipeline(['cygpath', '-w', url]).rstrip()
                url = 'file://' + url
        return url

    def cygpath(self, tb, cygwin):
        '''Do we have to call cygpath to transform local path to windows file
        system path?'''
        if tb or not cygwin:
            return False
        return (self.ui.app.name.find('/cygdrive/') == 0 and
                self.ui.app.name.find('/Cygwin/') < 0)

    def urlvisit(self):
        '''Visit url(s).'''
        textbrowsers = 'w3m', 'lynx', 'links', 'elinks'
        notty, screen, cygwin = False, False, util.cygwin()
        tb = self.appname in textbrowsers
        if tb:
            notty = not util.termconnected()
            screen = 'STY' in os.environ
        cygpath = self.cygpath(tb, cygwin)
        if not self.items:
            self.items = [self.ui.configitem('net', 'homepage')]
        self.items = [self.fixurl(url, cygpath) for url in self.items]
        # w3m does not need to be connected to terminal
        # but has to be connected if called into another screen instance
        if screen or self.appname in textbrowsers[1:] and notty:
            for url in self.items:
                util.systemcall([self.ui.app.name, url], notty, screen)
        else:
            for url in self.items:
                if not self.ui.app.open(url) and not cygwin:
                    # BROWSER=invalid gives valid
                    # webbrowser.GenericBrowser instance
                    # but returns False
                    # disable check for cygwin as valid
                    # graphical browser instances return False too
                    raise PybrowserError
