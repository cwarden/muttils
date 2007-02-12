# $Id$

from tformat import Tformat, TformatError
import os

def screendims():
    '''Get current term's columns and rows, return customized values.'''
    if os.uname()[0] == 'Darwin':
        p = os.popen('stty -a -f %s' % os.ctermid())
        tt = p.readline().split()
        t_rows = int(tt[3])
        t_cols = int(tt[5])
    else: # Linux
        p = os.popen('stty -a -F %s' % os.ctermid())
        tt = p.readline().split('; ')
        t_rows = int(tt[1].split()[1])
        t_cols = int(tt[2].split()[1])
    # rows: retain 2 lines for header + 1 for menu
    # cols need 1 extra when lines are broken
    return t_rows-3, t_cols+1


class IpagesError(TformatError):
    '''Exception class for ipages.'''

class ipages(Tformat):
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
        self.rows, self.cols = screendims()

    def softcount(self, item):
        '''Counts lines of item as displayed in
        a terminal with cols columns.'''
        lines = item.splitlines()
        return reduce(lambda a, b: a+b,
            [len(line)/self.cols + 1 for line in lines])

    def addpage(self, buff, lines):
        '''Adds a page to pages.'''
        self.pn += 1
        # fill page with newlines
        buff += '\n' * (self.rows-lines-1)
        self.pages[self.pn] = buff

    def pagesdict(self):
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
            raise IpagesError(e)
        # all this still supposes that no wrapped text item
        # has more lines than the terminal rows
        buff, lines = '', 0
        for item in items:
            ilines = self.softcount(item)
            linecheck = lines + ilines
            if linecheck < self.rows:
                buff += item
                lines = linecheck
            else:
                self.addpage(buff, lines)
                buff, lines = item, ilines
        self.addpage(buff, lines)
