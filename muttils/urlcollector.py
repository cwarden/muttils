# $Id$

import urlregex, util
import re, sys, urllib2

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
        if not self.files: # read from stdin
            self.findurls(sys.stdin.read())
        else:
            for f in self.files:
                f = util.absolutepath(f)
                try:
                    fp = urllib2.urlopen('file://%s' % f)
                except OSError, inst:
                    raise util.DeadMan(inst)
                try:
                    if fp.info().gettype().startswith('text/'):
                        self.findurls(fp.read())
                finally:
                    fp.close()
        if self.pat and self.items:
            try:
                self.pat = re.compile(r'%s' % self.pat, re.I)
            except re.error, err:
                raise util.DeadMan("%s in pattern `%s'" % (err, self.pat))
            self.items = filter(lambda i: self.pat.search(i), self.items)
