# $Id$

import iterm, util
import fcntl, os, struct, sys, termios

# format default paging command
pds = {-1:'Back', 1:'Forward'}

def valclamp(x, low, high):
    '''Clamps x between low and high.'''
    return max(low, min(x, high))


class tpager(object):
    '''
    Customizes interactive choice to current terminal.
    '''
    def __init__(self, items=None,
            name='item', format='sf', ckey='', qfunc='Quit', crit='pattern'):
        self.items = items or [] # (text) items to choose from
        self.name = name         # general name of an item
        if format in ('sf', 'bf'):
            self.format = format # sf: simple format, bf: bracket format
        else:
            raise util.DeadMan(
                    '%s: invalid format, use one of "sf", "bf"' % format)
        if not ckey or not ckey in 'qQ-':
            self.ckey = ckey     # key to customize pager
        else:
            raise util.DeadMan("the `%s' key is internally reserved." % ckey)
        self.qfunc = qfunc       # name of exit function
        self.crit = crit         # name of criterion for customizing
        self.pages =  {}         # dictionary of pages
        self.pn = 0              # current page/key of pages
        self.rows = 0            # terminal $LINES
        self.cols = 0            # terminal $COLUMNS
        self.notty = False       # True if not connected to terminal
        self.itemsdict = {}      # dictionary of items to choose
        self.ilen = 0            # length of items' list

    def terminspect(self):
        '''Get current term's columns and rows, return customized values.'''
        buf = 'abcd' # string length 4
        for dev in (sys.stdout, sys.stdin):
            fd = dev.fileno()
            istty = os.isatty(fd)
            if istty and buf == 'abcd':
                buf = fcntl.ioctl(fd, termios.TIOCGWINSZ, buf)
            elif not istty:
                self.notty = True
        if buf == 'abcd':
            raise util.DeadMan('could not get terminal size')
        t_rows, t_cols = struct.unpack('hh', buf) # 'hh': 2 signed short
        # rows: retain 1 line for header + 1 for menu
        # cols need 1 extra when lines are broken
        self.rows = t_rows-1
        self.cols = t_cols+1

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
        self.terminspect()
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

    def coltrunc(self, s, cols=0):
        '''Truncates string at beginning by inserting '>'
        if the string's width exceeds cols.'''
        mcols = cols or self.cols - 3
        slen = len(s)
        if slen <= mcols:
            return s
        else:
            return '>%s' % s[slen-mcols:]

    def pagedisplay(self, header, menu, pn=1):
        '''Displays a page of items including header and choice menu.'''
        sys.stdout.write(header + self.pages[pn])
        return raw_input(self.coltrunc(menu))

    def pagemenu(self):
        '''Lets user page through a list of items and make a choice.'''
        header = self.coltrunc('*%d %s*\n'
                % (self.ilen, self.name+'s'[self.ilen==1:]), self.cols - 2)
        plen = len(self.pages)
        if plen == 1: # no paging
            cs = ', ^C:Cancel'
            if self.ckey:
                cs += ', %s<%s>' % (self.ckey, self.crit)
            if self.itemsdict:
                cs += ', Number'
            menu = 'Page 1 of 1 [%s]%s ' % (self.qfunc, cs)
            reply = self.pagedisplay(header, menu)
            if reply in self.itemsdict:
                self.items = [self.itemsdict[reply]]
            elif not reply:
                self.items = []
            elif not self.ckey or not reply.startswith(self.ckey):
                reply = self.pagemenu() # display same page
        else: # more than 1 page
            pn = 1 # start at first page
            pdir = -1 # initial paging direction reversed
            while True:
                bs = '' # reverse paging direction
                if 1 < pn < plen:
                    bs = '-:%s, ' % pds[pdir*-1]
                else:
                    pdir *= -1
                menu = 'Page %d of %d [%s], ^C:Cancel, %sq:%s' % (pn, plen,
                        pds[pdir], bs, self.qfunc)
                if self.ckey:
                    menu += ', %s<%s>' % (self.ckey, self.crit)
                menu += ', Number '
                reply = self.pagedisplay(header, menu, pn)
                if not reply:
                    pn = valclamp(pn+pdir, 1, plen)
                elif bs and reply == '-':
                    pdir *= -1
                    pn = valclamp(pn+pdir, 1, plen)
                elif reply in self.itemsdict:
                    self.items = [self.itemsdict[reply]]
                    break
                elif reply in 'qQ':
                    self.items = []
                    break
                elif self.ckey and reply.startswith(self.ckey):
                    break
                #else: same page displayed on invalid response
        return reply

    def interact(self):
        self.pagesdict()
        if self.notty:
            it = iterm.iterm()
            it.terminit()
        try:
            retval = self.pagemenu()
        except KeyboardInterrupt:
            retval, self.items = '', None
        if self.notty:
            it.reinit()
        return retval
