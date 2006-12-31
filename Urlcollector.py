# $Id$

import re, sys
from Urlregex import Urlregex, UrlregexError

class UrlcollectorError(Exception):
    '''Exception class for the Urlcollector module.'''

class Urlcollector(Urlregex):
    '''
    Provides function to retrieve urls
    from files or input stream.
    '''
    def __init__(self, proto='all'):
        Urlregex.__init__(self, proto=proto) # <- proto, decl, items
        self.files = []         # files to search
        self.pat = None         # pattern to match urls against

    def urlCollect(self):
        '''Harvests urls from stdin or files.'''
        def urlFind(data):
            try:
                self.findUrls(data)
            except UrlregexError, e:
                raise UrlcollectorError(e)

        if not self.files: # read from stdin
            urlFind(sys.stdin.read())
        else:
            import datatype
            for f in self.files:
                data, kind = datatype.dataType(f)
                if kind.startswith('text/'):
                    urlFind(data)
        if self.pat and self.items:
            try:
                self.pat = re.compile(r'%s' % self.pat, re.I)
            except re.error, e:
                raise UrlcollectorError("%s in pattern `%s'" % (e, self.pat))
            self.items = filter(lambda i: self.pat.search(i), self.items)
