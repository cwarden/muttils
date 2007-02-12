# $Id$

import urlregex, util
import re, sys, urllib2

class UrlcollectorError(Exception):
    '''Exception class for the urlcollector module.'''

class urlcollector(urlregex.urlregex):
    '''
    Provides function to retrieve urls
    from files or input stream.
    '''
    def __init__(self, proto='all', decl=False, files=None, pat=None):
        urlregex.urlregex.__init__(self, proto=proto, decl=decl)
        # ^ items
        self.files = files or [] # files to search
        self.pat = pat           # pattern to match urls against

    def urlcollect(self):
        '''Harvests urls from stdin or files.'''
        def urlfind(data):
            try:
                self.findurls(data)
            except urlregex.UrlregexError, inst:
                raise UrlcollectorError(inst)

        if not self.files: # read from stdin
            urlfind(sys.stdin.read())
        else:
            for f in self.files:
                f = util.absolutepath(f)
                fp = urllib2.urlopen('file://%s' % f)
                try:
                    if fp.info().gettype().startswith('text/'):
                        urlfind(fp.read())
                finally:
                    fp.close()
        if self.pat and self.items:
            try:
                self.pat = re.compile(r'%s' % self.pat, re.I)
            except re.error, e:
                raise UrlcollectorError("%s in pattern `%s'" % (e, self.pat))
            self.items = filter(lambda i: self.pat.search(i), self.items)
