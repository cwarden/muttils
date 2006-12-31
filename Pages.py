# $Id$

from tpager import terminfo
from tpager.Tformat import Tformat, TformatError

class PagesError(TformatError):
    '''Exception class for Pages.'''

class Pages(Tformat):
    '''
    Subclass for Tpager.
    Provides items, ilen, pages, itemsdict, cols.
    '''
    def __init__(self, format='sf'):
        Tformat.__init__(self, format=format)  # <- format, itemsdict, keys
        self.items = []                 # (text) items to choose from
        self.ilen = 0                   # length of items' list
        self.pages =  {}                # dictionary of pages
        self.pn = 0                     # current page/key of pages
        self.cols = terminfo.t_cols+1   # needs 1 extra when lines are broken
        self.rows = terminfo.t_rows-3   # retain 2 lines for header & 1 for menu

    def softCount(self, item):
        '''Counts lines of item as displayed in
        a terminal with cols columns.'''
        lines = item.splitlines()
        return reduce(lambda a, b: a+b,
            [len(line)/self.cols + 1 for line in lines])

    def addPage(self, buff, lines):
        '''Adds a page to pages.'''
        self.pn += 1
        # fill page with newlines
        buff += '\n' * (self.rows-lines-1)
        self.pages[self.pn] = buff

    def pagesDict(self):
        '''Creates dictionary of pages to display in terminal window.
        Keys (page numbers) are integers starting from 1.'''
        self.itemsdict, self.pages, self.pn = {}, {}, 0
        self.ilen = len(self.items)
        numkeys = xrange(1, self.ilen+1)
        self.keys = map(str, numkeys)
        map(self.itemsdict.__setitem__, self.keys, self.items)
        try:
            items = self.formatItems()
        except TformatError, e:
            raise PagesError(e)
        # all this still supposes that no wrapped text item
        # has more lines than the terminal rows
        buff, lines = '', 0
        for item in items:
            ilines = self.softCount(item)
            linecheck = lines + ilines
            if linecheck < self.rows:
                buff += item
                lines = linecheck
            else:
                self.addPage(buff, lines)
                buff, lines = item, ilines
        self.addPage(buff, lines)
