# $Id$

import os, sys
try:
    # termios only available for unix
    import termios, array, fcntl, signal
except ImportError:
    pass

from muttils import iterm, util

def _gettyenv(v):
    try:
        return int(os.environ[v])
    except (KeyError, ValueError):
        pass

class tpager(object):
    '''
    Customizes interactive choice to current terminal.
    '''
    pages =  {}         # dictionary of pages
    fd = None           # file descriptor reference for resizing term
    rows = 0            # terminal $LINES
    cols = 0            # terminal $COLUMNS
    itemsdict = {}      # dictionary of items to choose
    ilen = 0            # length of items' list
    more = False        # more than 1 page
    plen = 0            # how many pages

    def __init__(self, ui, items=None, name='item',
                 format='sf', ckey='', qfunc='quit', crit='pattern'):
        self.ui = ui
        self.items = items or [] # (text) items to choose from
        self.name = name         # general name of an item
        self.format = format
        if self.format not in ('sf', 'bf'):
            raise util.DeadMan('%s: invalid format, use one of "sf", "bf"'
                               % self.format)
        self.ckey = ckey         # key to customize pager
        if self.ckey in ('q', 'Q', '-'):
            raise util.DeadMan("the `%s' key is internally reserved."
                               % self.ckey)
        self.qfunc = qfunc       # name of exit function
        self.crit = crit         # name of criterion for customizing

    def ttysize(self):
        arrini = fcntl.ioctl(self.fd, termios.TIOCGWINSZ, '\0' * 8)
        self.rows, self.cols = array.array('h', arrini)[:2]
        # rows: retain 1 line for header + 1 for menu
        # cols need 1 extra when lines are broken
        self.rows -= 1
        self.cols += 1

    def resizehandler(self, signalnum, frame):
        self.ttysize()
        self.pagesdict()

    def terminspect(self):
        '''Get current term's columns and rows, return customized values.'''
        notty = False  # assume connection to terminal
        self.fd = None # reset if class was not reloaded (ckey)
        for dev in (sys.stdout, sys.stdin):
            try:
                fd = dev.fileno()
                istty =  os.isatty(fd)
                if not istty:
                    notty = True
                elif not self.fd:
                    self.fd = fd
            except ValueError:
                # I/O operation on closed file
                notty = True
        if self.fd is not None:
            try:
                if not notty:
                    self.resizehandler(None, None)
                    signal.signal(signal.SIGWINCH, self.resizehandler)
                else:
                    self.ttysize()
                    if notty:
                        self.fd = None
            except NameError:
                self.fd = None
        self.rows = self.rows or (_gettyenv('LINES') or 24) - 1
        self.cols = self.cols or (_gettyenv('COLUMNS') or 80) + 1
        return notty

    def formatitems(self):
        '''Formats items of itemsdict to numbered list.'''
        def simpleformat(key):
            return '%s) %s\n' % (key.rjust(maxl), self.itemsdict[key])

        def bracketformat(key):
            return '[%s]\n%s\n' % (key, self.itemsdict[key])

        self.ilen = len(self.items)
        ikeys = [str(i) for i in xrange(1, self.ilen+1)]
        self.itemsdict = dict(zip(ikeys, self.items))
        if self.format != 'bf':
            maxl = len(ikeys[-1])
            formfunc = simpleformat
        else:
            formfunc = bracketformat
        for k in ikeys:
            yield formfunc(k)

    def addpage(self, buff, lines, pn):
        pn += 1
        if self.more:
            # fill page with newlines
            buff += '\n' * (self.rows-lines-1)
        self.pages[pn] = buff
        return pn

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
            ilines = sum([len(line)/self.cols for line in ilines], len(ilines))
            linecheck = lines + ilines
            if linecheck < self.rows:
                buff += item
                lines = linecheck
            else:
                self.more = True
                pn = self.addpage(buff, lines, pn)
                buff, lines = item, ilines
        pn = self.addpage(buff, lines, pn)
        self.plen = len(self.pages)

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

    def clamp(self, pn):
        '''Returns number of next page.'''
        return max(1, min(pn, self.plen))

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
            pn = 1 # start at first page
            pdir = -1 # initial paging direction reversed
            while True:
                bs = '' # reverse paging direction
                if self.plen > 1:
                    if 1 < pn < self.plen:
                        bs = '-:%s, ' % pds[pdir*-1]
                    else:
                        pdir *= -1
                    menu = ('page %d of %d [%s], ^C:cancel, %sq:%s'
                            % (pn, self.plen, pds[pdir], bs, self.qfunc))
                else:
                    # items selected by self.crit might fit on 1 page
                    menu = '^C:cancel, q:%s' % self.qfunc
                if self.ckey:
                    menu += ', %s<%s>' % (self.ckey, self.crit)
                menu += ', number '
                reply = self.pagedisplay(header, menu, pn)
                if not reply:
                    pn = self.clamp(pn+pdir)
                elif bs and reply == '-':
                    pdir *= -1
                    pn = self.clamp(pn+pdir)
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
        if self.fd is not None:
            signal.signal(signal.SIGWINCH, signal.SIG_DFL)
        return retval
