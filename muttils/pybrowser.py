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

def weburlregex():
    '''Returns regex matching web url.'''
    u = urlregex.urlregex(proto='web', uniq=False)
    u.urlobject(search=False)
    return u.url_re


class browser(object):
    '''
    Visits items with default or given browser.
    '''
    def __init__(self, parentui=None, items=None, app=''):
        self.ui = parentui or ui.config()
        self.items = items # urls
        self.app = app     # browser app
        self.conny = False # try to connect to net
        self.weburl_re = weburlregex() # check remote url protocol scheme
        self.local_re = None           # check local protocol scheme
        self.file_re = None            # strip file url

    def get_localre(self):
        '''Compiles local_re on demand and returns it.'''
        if not self.local_re:
            self.local_re = re.compile('http://(%s)'
                    % '|'.join(re.escape(a) for a in getlocals()),
                    re.IGNORECASE)
        return self.local_re

    def mkfileurl(self, url):
        '''Compiles file_re on demand and returns it.'''
        if not self.file_re:
            self.file_re = re.compile(r'file:/+', re.IGNORECASE)
        # strip url to pure pathname
        url = self.file_re.sub('/', url, 1)
        url = util.absolutepath(url)
        if not url.startswith('/'):
            url = os.path.join(os.getcwd, url)
        if not os.path.exists(url):
            raise util.DeadMan('%s: file not found' % url)
        return 'file://%s' % url

    def urlcomplete(self, url):
        '''Adapts possibly short url to pass as browser argument.'''
        if self.weburl_re.match(url):
            self.conny = True
            url = urlregex.webschemecomplete(url)
        elif not self.get_localre().match(url):
            url = self.mkfileurl(url)
        return url

    def urlvisit(self):
        '''Visit url(s).'''
        if not self.items:
            self.ui.updateconfig()
            self.items = [self.ui.configitem('net', 'homepage')]
        self.items = [self.urlcomplete(url) for url in self.items]
        try:
            if self.app:
                b = webbrowser.get(self.app)
            else:
                b = webbrowser.get()
            if self.conny:
                util.goonline()
            for url in self.items:
                b.open(url)
        except webbrowser.Error, inst:
            raise util.DeadMan(inst)
