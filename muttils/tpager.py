# $Id$

import iterm, util
import os, sys
try:
    # termios only available for unix
    import termios, array, fcntl
except ImportError:
    pass

def valclamp(x, low, high):
    '''Clamps x between low and high.'''
    return max(low, min(x, high))


class tpager(object):
    '''
    Customizes interactive choice to current terminal.
    '''
    pages =  {}         # dictionary of pages
    rows = 0            # terminal $LINES
    cols = 0            # terminal $COLUMNS
    itemsdict = {}      # dictionary of items to choose
    ilen = 0            # length of items' list
    more = False        # more than 1 page

    def __init__(self, ui, items=None, name='item',
                 format='sf', ckey='', qfunc='quit', crit='pattern'):
        self.ui = ui
        self.items = items or [] # (text) items to choose from
        self.name = name         # general name of an item
        if format in ('sf', 'bf'):
            self.format = format # sf: simple format, bf: bracket format
        else:
            raise util.DeadMan('%s: invalid format, use one of "sf", "bf"'
                    % format)
        if not ckey or not ckey in 'qQ-':
            self.ckey = ckey     # key to customize pager
        else:
            raise util.DeadMan("the `%s' key is internally reserved." % ckey)
        self.qfunc = qfunc       # name of exit function
        self.crit = crit         # name of criterion for customizing

    def terminspect(self):
        '''Get current term's columns and rows, return customized values.'''
        def _gettyenv(v):
            if v in os.environ:
                try:
                    return int(os.environ[v])
                except TypeError:
                    return 0
            return 0

        def _missing():
            return (not self.rows or not self.cols)

        self.rows = _gettyenv('LINES')
        self.cols = _gettyenv('COLUMNS')
        rows = cols = 0
        notty = False # assume connection to terminal
        for dev in (sys.stdout, sys.stdin):
            try:
                fd = dev.fileno()
                istty =  os.isatty(fd)
                if _missing() and istty:
                    arrini = fcntl.ioctl(fd, termios.TIOCGWINSZ, '\0' * 8)
                    rows, cols = array.array('h', arrini)[:2]
                elif not istty:
                    notty = True
            except ValueError:
                # I/O operation on closed file
                notty = True
            except NameError:
                pass
        if _missing():
            # still prefer env
            self.rows = self.rows or rows
            self.cols = self.cols or cols
            if _missing():
                msg = ('could not obtain terminal size\n'
                       'try setting $LINES and $COLUMNS environment')
                raise util.DeadMan(msg)
        # rows: retain 1 line for header + 1 for menu
        # cols need 1 extra when lines are broken
        self.rows -= 1
        self.cols += 1
        return notty

    def addpage(self, buff, lines, pn):
        '''Adds a page to pages and returns pageno.'''
        pn += 1
        if self.more:
            # fill page with newlines
            buff += '\n' * (self.rows-lines-1)
        self.pages[pn] = buff
        return pn

    def formatitems(self):
        '''Formats items of itemsdict to numbered list.'''
        if not self.items:
            return []

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
        self.itemsdict = dict(zip(ikeys, self.items))
        if self.format == 'sf':
            maxl = len(ikeys[-1])
        formatfunc = formdict[self.format]
        return [formatfunc(k) for k in ikeys]

    def pagesdict(self):
        '''Creates dictionary of pages to display in terminal window.
        Keys are integers as string starting from "1".'''
        self.itemsdict.clear()
        self.pages.clear()
        # all this still supposes that no wrapped text item
        # has more lines than the terminal rows
        buff, lines, pn = '', 0, 0
        for item in self.formatitems():
            # lines of item, taking overruns into account
            ilines = item.splitlines()
            ilines = reduce(lambda a, b: a+b,
                            [len(line)/self.cols + 1 for line in ilines])
            linecheck = lines + ilines
            if linecheck < self.rows:
                buff += item
                lines = linecheck
            else:
                self.more = True
                pn = self.addpage(buff, lines, pn)
                buff, lines = item, ilines
        pn = self.addpage(buff, lines, pn)

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
        self.ui.write(header + self.pages[pn])
        return raw_input(self.coltrunc(menu))

    def pagemenu(self):
        '''Lets user page through a list of items and make a choice.'''
        header = self.coltrunc('*%s*\n' % util.plural(self.ilen, self.name),
                               self.cols - 2)
        if not self.more:
            cs = ', ^C:cancel'
            if self.ckey:
                cs += ', %s<%s>' % (self.ckey, self.crit)
            if self.itemsdict:
                cs += ', number'
            menu = '[%s]%s ' % (self.qfunc, cs)
            reply = self.pagedisplay(header, menu)
            if reply in self.itemsdict:
                self.items = [self.itemsdict[reply]]
            elif not reply:
                self.items = []
            elif not self.ckey or not reply.startswith(self.ckey):
                reply = self.pagemenu() # display same page
        else: # more than 1 page
            # switch paging command according to paging direction
            pds = {-1: 'back', 1: 'forward'}
            plen = len(self.pages)
            pn = 1 # start at first page
            pdir = -1 # initial paging direction reversed
            while True:
                bs = '' # reverse paging direction
                if plen > 1:
                    if 1 < pn < plen:
                        bs = '-:%s, ' % pds[pdir*-1]
                    else:
                        pdir *= -1
                    menu = ('page %d of %d [%s], ^C:cancel, %sq:%s'
                            % (pn, plen, pds[pdir], bs, self.qfunc))
                else:
                    # items selected by self.crit might fit on 1 page
                    menu = '^C:cancel, q:%s' % self.qfunc
                if self.ckey:
                    menu += ', %s<%s>' % (self.ckey, self.crit)
                menu += ', number '
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
        notty = self.terminspect()
        self.pagesdict()
        if notty:
            it = iterm.iterm()
            it.terminit()
        try:
            retval = self.pagemenu()
        except KeyboardInterrupt:
            retval, self.items = '', None
        if notty:
            it.reinit()
        return retval
