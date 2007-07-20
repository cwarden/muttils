# $Id$

'''html2text.py - dead simple html to text conversion
'''

import util
import cStringIO, formatter, htmllib

class html2text(htmllib.HTMLParser):
    '''
    Provides methods for very simple html to text conversion.
    '''
    fp = None
    formatter = None

    def __init__(self, strict=False):
        '''Initializes parser and opens file object.'''
        self.strict = strict
        htmllib.HTMLParser.__init__(self, formatter=self.formatter)

    def open(self):
        self.fp = cStringIO.StringIO()
        writer = formatter.DumbWriter(file=self.fp)
        self.formatter = formatter.AbstractFormatter(writer=writer)

    def feed(self, ht):
        '''Passes hypertext thru parser,
        overriding HTMLParser's feed method.'''
        try:
            htmllib.HTMLParser.feed(self, ht)
        except htmllib.HTMLParseError, inst:
            if not self.strict:
                pass
            else:
                raise util.DeadMan(inst)
    
    def htwrite(self, ht='', append=False):
        '''Writes converted text to file object.'''
        if not append:
            self.fp.truncate(0)
        self.feed(ht)

    def htwritelines(self, linelist=None, append=False):
        '''Writes a list of lines to file object.'''
        lines = linelist or []
        if not append:
            self.fp.truncate(0)
        for line in lines:
            self.feed(line)

    def htread(self):
        '''Returns converted text.'''
        return self.fp.getvalue()

    def htreadlines(self, nl=True):
        '''Returns converted lines of text.'''
        return self.fp.getvalue().splitlines(nl)

    def close(self):
        '''Closes parser and file object,
        overriding HTMLParser's close method but calling it.'''
        htmllib.HTMLParser.close(self)
        self.fp.close()
