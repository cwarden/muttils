# $Id$

import util
import subprocess

def screendims():
    '''Get current term's columns and rows, return customized values.'''
    p = subprocess.Popen(['tput', 'lines'], close_fds=True,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    t_rows = p.stdout.readline()
    p = subprocess.Popen(['tput', 'cols'], close_fds=True,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    t_cols = p.stdout.readline()
    # rows: retain 2 lines for header + 1 for menu
    # cols need 1 extra when lines are broken
    return int(t_rows)-3, int(t_cols)+1


class ipages(object):
    '''
    Subclass for tpager.
    Provides items, format, pages, cols, itemsdict, ilen for tpager.
    '''
    def __init__(self, items=None, format='sf'):
        self.items = items or [] # (text) items to choose from
        self.format = format     # sf: simple format, bf: bracket format
        self.pages =  {}         # dictionary of pages
        self.pn = 0              # current page/key of pages
        self.rows, self.cols = screendims()
        self.itemsdict = {}      # dictionary of items to choose
        self.ilen = 0            # length of items' list

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

    def formatitems(self):
        '''Formats items of itemsdict to numbered list.'''

        def simpleformat(key):
            '''Simple format of choice menu,
            recommended for 1 line items.'''
            return '%s) %s\n' % (key.rjust(maxl), self.itemsdict[key])
        def bracketformat(key):
            '''Format of choice menu with items
            that are longer than 1 line.'''
            return '[%s]\n%s\n' % (key, self.itemsdict[key])

        formdict = {'sf': simpleformat, 'bf': bracketformat}
        if self.format not in formdict:
            raise util.DeadMan('%s: invalid format, use one of "sf", "bf"'
                    % self.format)

        self.ilen = len(self.items)
        ikeys = [str(i) for i in xrange(1, self.ilen+1)]
        map(self.itemsdict.__setitem__, ikeys, self.items)
        if not self.itemsdict:
            return []
        maxl = len(ikeys[-1])
        formatfunc = formdict[self.format]
        return [formatfunc(k) for k in ikeys]

    def pagesdict(self):
        '''Creates dictionary of pages to display in terminal window.
        Keys are integers as string starting from "1".'''
        self.itemsdict, self.pages, self.pn = {}, {}, 0
        items = self.formatitems()
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
