# $Id$

import ipages, iterm
import os

# format default paging command
pds = {-1:'Back', 1:'Forward'}

def valclamp(x, low, high):
    '''Clamps x between low and high.'''
    return max(low, min(x, high))


class TpagerError(Exception):
    '''Exception class for Tpager module.'''

class tpager(ipages.ipages):
    '''
    Customizes interactive choice to current terminal.
    '''
    def __init__(self, items=None,
            name='item', format='sf', qfunc='Quit', ckey='', crit='pattern'):
        ipages.ipages.__init__(self, items=items, format=format)
        # ^ items, ilen, pages, itemsdict, cols
        self.name = name            # general name of an item
        self.qfunc = qfunc          # name of exit function
        if ckey and ckey in 'qQ-':
            raise TpagerError("the `%s' key is internally reserved." % ckey)
        else:
            self.ckey = ckey        # key to customize pager
        self.crit = crit            # criterion for customizing
        self.header = ''

    def coltrunc(self, s, cols=0):
        '''Truncates string at beginning by inserting '>'
        if the string's width exceeds cols.'''
        mcols = cols or self.cols - 3
        slen = len(s)
        if slen <= mcols:
            return s
        else:
            return '>%s' % s[slen-mcols:]

    def pagedisplay(self, menu, pn=1):
        '''Displays a page of items including header and choice menu.'''
        print self.header + self.pages[pn]
        return raw_input(self.coltrunc(menu))

    def pagemenu(self):
        '''Lets user page through a list of items and make a choice.'''
        self.header = self.coltrunc('*%d %s*\n\n'
                % (self.ilen, self.name+'s'[self.ilen==1:]), self.cols - 2)
        plen = len(self.pages)
        if plen == 1: # no paging
            cs = ', ^C:Cancel'
            if self.ckey:
                cs += ', %s<%s>' % (self.ckey, self.crit)
            if self.itemsdict:
                cs += ', Number'
            menu = 'Page 1 of 1 [%s]%s ' % (self.qfunc, cs)
            reply = self.pagedisplay(menu)
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
                reply = self.pagedisplay(menu, pn)
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
        try:
            self.pagesdict()
        except ipages.IpagesError, e:
            raise TpagerError(e)
        notty = not os.isatty(0) or not os.isatty(1) # not connected to term
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
