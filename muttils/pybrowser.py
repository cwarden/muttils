# $Id$

import ui, urlregex, util
import os, webbrowser

class browser(object):
    '''
    Visits items with default or given browser.
    '''
    weburl_re = None          # url protocol scheme regex

    def __init__(self, parentui=None, items=None, app='', evalurl=False):
        self.ui = parentui or ui.ui()
        self.ui.updateconfig()
        self.items = items             # urls
        if app:
            self.ui.app = app          # browser app from command-line
        if evalurl: # check remote url protocol scheme
            self.ui.proto = 'web'
            u = urlregex.urlregex(self.ui, uniq=False)
            u.urlobject(search=False)
            self.weburl_re = u.url_re

    def fixurl(self, url):
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
                # as some browser don't handle file scheme gracefully
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
        return url

    def urlvisit(self):
        '''Visit url(s).'''
        textbrowsers = ('w3m', 'lynx', 'links', 'elinks')
        if not self.items:
            self.items = [self.ui.configitem('net', 'homepage')]
        self.items = map(self.fixurl, self.items)
        app = os.path.basename(self.ui.app)
        screen = app in textbrowsers and 'STY' in os.environ
        notty = not util.termconnected()
        # w3m does not need to be connected to terminal
        # but has to be connected if called into another screen instance
        if screen or app in textbrowsers[1:] and notty:
            for url in self.items:
                util.systemcall([self.ui.app, url], notty, screen)
        else:
            try:
                if self.ui.app:
                    b = webbrowser.get(self.ui.app)
                else:
                    b = webbrowser.get()
                for url in self.items:
                    b.open(url)
            except webbrowser.Error, inst:
                raise util.DeadMan(inst)
