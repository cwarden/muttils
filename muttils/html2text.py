# $Id$

from cStringIO import StringIO
from formatter import DumbWriter, AbstractFormatter
from htmllib import HTMLParser, HTMLParseError

class HTML2TextError(Exception):
    '''Exception class for the html2text module.'''

class HTML2Text(HTMLParser):
    '''
    Provides methods for very simple html to text conversion.
    '''
    def __init__(self, strict=False):
        '''Initializes parser and opens file object.'''
        self.strict = strict
        self.fp = None
        self.formatter = None
        HTMLParser.__init__(self, formatter=self.formatter)

    def open(self):
        self.fp = StringIO()
        writer = DumbWriter(file=self.fp)
        self.formatter = AbstractFormatter(writer=writer)

    def feed(self, html):
        '''Passes hypertext thru parser,
        overriding HTMLParser's feed method.'''
        try:
            HTMLParser.feed(self, html)
        except HTMLParseError, e:
            if not self.strict:
                pass
            else:
                raise HTML2TextError(e)
    
    def htpWrite(self, html='', append=False):
        '''Writes converted text to file object.'''
        if not append:
            self.fp.truncate(0)
        self.feed(html)

    def htpWritelines(self, linelist=None, append=False):
        '''Writes a list of lines to file object.'''
        if linelist is None:
            linelist = []
        if not append:
            self.fp.truncate(0)
        for line in linelist:
            self.htpWrite(html=line, append=True)

    def htpRead(self):
        '''Returns converted text.'''
        return self.fp.getvalue()

    def htpReadlines(self, nl=True):
        '''Returns converted lines of text.'''
        return self.fp.getvalue().splitlines(nl)

    def close(self):
        '''Closes parser and file object,
        overriding HTMLParser's close method but calling it.'''
        HTMLParser.close(self)
        self.fp.close()
