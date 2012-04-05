# $Id$

import os, webbrowser
from muttils import ui, urlregex, util

class browser(object):
    '''
    Visits items with default or given browser.
    '''
    weburl_re = None          # url protocol scheme regex

    def __init__(self, parentui=None, items=None, app=None, evalurl=False):
        self.ui = parentui or ui.ui()
        self.ui.updateconfig()
        self.items = items             # urls
        if app is not None:
            self.ui.app = app
        if evalurl: # check remote url protocol scheme
            self.ui.proto = 'web'
            u = urlregex.urlregex(self.ui, uniq=False)
            u.urlobject(search=False)
            self.weburl_re = u.url_re

    def fixurl(self, url, cygpath):
        '''Adapts possibly short url to pass as browser argument.'''
        if not self.weburl_re or self.weburl_re.match(url):
            url = urlregex.webschemecomplete(url)
            gophers = ('lynx', 'firefox')
            if url.startswith('gopher://') and self.ui.app not in gophers:
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
            if not url.startswith('http://'):
                url = util.absolutepath(url)
                if not os.path.exists(url):
                    raise util.DeadMan('%s: not found' % url)
                if cygpath:
                    url = util.pipeline(['cygpath', '-w', url]).rstrip()
                url = 'file://' + url
        return url

    def cygpath(self, tb):
        '''Do we have to call cygpath to transform local path to windows file
        system path?'''
        if not util.cygwin() or tb:
            return False
        app = self.ui.app
        if app is None:
            try:
                app = os.environ['BROWSER']
            except KeyError:
                hint = '$BROWSER environment variable required on cygwin'
                raise util.DeadMan('cannot detect system browser', hint=hint)
        return app.find('/cygdrive/') == 0 and app.find('/Cygwin/') < 0

    def urlvisit(self):
        '''Visit url(s).'''
        textbrowsers = 'w3m', 'lynx', 'links', 'elinks'
        app, tb, notty, screen = '', False, False, False
        if self.ui.app is not None:
            app = os.path.basename(self.ui.app)
            tb = app in textbrowsers
            if tb:
                notty = not util.termconnected()
                screen = 'STY' in os.environ
        cygpath = self.cygpath(tb)
        if not self.items:
            self.items = [self.ui.configitem('net', 'homepage')]
        self.items = [self.fixurl(url, cygpath) for url in self.items]
        # w3m does not need to be connected to terminal
        # but has to be connected if called into another screen instance
        if screen or app in textbrowsers[1:] and notty:
            for url in self.items:
                util.systemcall([self.ui.app, url], notty, screen)
        else:
            try:
                b = webbrowser.get(self.ui.app)
                for url in self.items:
                    b.open(url)
            except webbrowser.Error, inst:
                raise util.DeadMan(inst)
