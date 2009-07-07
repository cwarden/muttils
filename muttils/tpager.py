# $Id$

import os, sys
try:
    # termios only available for unix
    import termios, array, fcntl, signal
except ImportError:
    pass

from muttils import iterm, util

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
                 fmt='sf', ckey='', qfunc='quit', crit='pattern'):
        self.ui = ui
        self.items = items or [] # (text) items to choose from
        self.name = name         # general name of an item
        self.fmt = fmt
        if self.fmt not in ('sf', 'bf'):
            raise util.DeadMan('%s: invalid format, use one of "sf", "bf"'
                               % self.fmt)
        self.ckey = ckey         # key to customize pager
        if self.ckey in ('q', 'Q', '-'):
            raise util.DeadMan("the `%s' key is internally reserved."
                               % self.ckey)
        self.qfunc = qfunc       # name of exit function
        self.crit = crit         # name of criterion for customizing

    def kmaxl(self):
        '''Returns string length of highest current itemsdict key.'''
        return len(str(len(self.itemsdict)))

    def formatitems(self):
        '''Formats items of itemsdict to numbered list.'''
        def simpleformat(k, v):
            return '%s) %s\n' % (str(k).rjust(maxl), v)

        def bracketformat(k, v):
            return '[%d]\n%s\n' % (k, v)

        self.ilen = len(self.items)
        if self.fmt != 'bf':
            maxl = self.kmaxl()
            formfunc = simpleformat
        else:
            formfunc = bracketformat
        self.itemsdict = dict(enumerate(self.items))
        for k, v in self.itemsdict.iteritems():
            yield formfunc(k + 1, v)

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
            ilines = sum((len(line)/self.cols for line in ilines), len(ilines))
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

    def choice(self, header, menu, pn=1):
        '''Displays a page of items, header and choice menu.
        Returns response and validity of choice.'''
        self.ui.write(header + self.pages[pn])
        resp = raw_input(self.coltrunc(menu, self.cols - self.kmaxl() - 3))
        valid = True
        try:
            self.items = [self.itemsdict[int(resp) - 1]]
        except (ValueError, KeyError):
            if self.more and resp in ('q', 'Q') or not self.more and not resp:
                # quit
                self.items = []
            else:
                # user command is a valid response
                valid = self.ckey and resp.startswith(self.ckey)
        return resp, valid

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
            resp, valid = self.choice(header, menu)
            if valid:
                return resp
            return self.pagemenu()
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
                resp, valid = self.choice(header, menu, pn)
                if valid:
                    return resp
                if resp == '-' and bs or resp and pn in (1, self.plen):
                    # on first and last page with invalid response
                    # preemptively switch direction
                    pdir *= -1
                pn = max(1, min(pn + pdir, self.plen))

    def ttysize(self):
        arrini = fcntl.ioctl(self.fd, termios.TIOCGWINSZ, '\0' * 8)
        self.rows, self.cols = array.array('h', arrini)[:2]

    def resizehandler(self, signalnum, frame):
        self.ttysize()
        self.pagesdict()

    def terminspect(self):
        '''Get current term's columns and rows, return customized values.'''
        notty = False  # assume connection to terminal
        self.fd = None # reset if class was not reloaded (ckey)
        for dev in (sys.stdout, sys.stdin):
            try:
                if not dev.isatty():
                    notty = True
                elif not self.fd:
                    self.fd = dev.fileno()
            except ValueError:
                # I/O operation on closed file
                notty = True
        try:
            self.rows = int(os.environ['LINES'])
            self.cols = int(os.environ['COLUMNS'])
        except (KeyError, ValueError):
            if self.fd is not None:
                try:
                    if notty:
                        self.ttysize()
                        self.fd = None
                    else:
                        self.resizehandler(None, None)
                        signal.signal(signal.SIGWINCH, self.resizehandler)
                except NameError:
                    self.fd = None
                    self.rows = 24
                    self.cols = 80
        # rows: retain 1 line for header + 1 for menu
        # cols need 1 extra when lines are broken
        self.rows -= 1
        self.cols += 1
        return notty

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
