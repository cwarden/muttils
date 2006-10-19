# $Hg: Pages.py,v$

import terminfo
from Tformat import Tformat

class Pages(Tformat):
    '''
    Subclass for Tpager.
    Provides items, ilen, pages, itemsdict, cols.
    '''
    def __init__(self, format='sf'):
        Tformat.__init__(self)          # <- format, itemsdict, keys
        self.format = format
        self.items = []                 # (text) items to choose from
        self.ilen = 0                   # length of items' list
        self.pages =  {}                # dictionary of pages
        self.item = ''                  # current text item
        self.pn = 0                     # current page/key of pages
        self.buff = ''                  # current page string buffer
        self.lines = 0                  # current amount of lines
        self.cols = terminfo.t_cols+1   # needs 1 extra when lines are broken
        self.rows = terminfo.t_rows-3   # retain 2 lines for header & 1 for menu

    def itemsDict(self):
        '''Populates itemsdict and keys.'''
        self.ilen = len(self.items)
        numkeys = xrange(1, self.ilen+1)
        self.keys = map(str, numkeys)
        map(self.itemsdict.__setitem__, self.keys, self.items)

    def softCount(self):
        '''Counts lines of item as displayed in
        a terminal with cols columns.'''
        lines = self.item.splitlines()
        return reduce(lambda a, b: a+b,
            [len(line)/self.cols + 1 for line in lines])

    def addPage(self):
        '''Adds a page to pages.'''
        self.pn += 1
        # fill page with newlines
        self.buff += '\n' * (self.rows-self.lines-1)
        self.pages[self.pn] = self.buff

    def pagesDict(self):
        '''Creates dictionary of pages to display in terminal window.
        Keys (page numbers) are integers starting from 1.'''
        self.itemsDict()
        items = Tformat.formatItems(self)
        # all this still supposes that no wrapped text item
        # has more lines than the terminal rows
        for self.item in items:
            ilines = self.softCount()
            linecheck = self.lines + ilines
            if linecheck < self.rows:
                self.buff += self.item
                self.lines = linecheck
            else:
                self.addPage()
                self.buff, self.lines = self.item, ilines
        self.addPage()
