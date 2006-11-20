# $Hg: Tpager.py,v$

from Pages import Pages
from cheutils import spl, valclamp

# format default paging command
pds = {-1:'Back', 1:'Forward'}

class TpagerError(Exception):
    '''Exception class for Tpager module.'''

class Tpager(Pages):
    '''
    Customizes interactive choice to current terminal.
    '''
    def __init__(self, name='item', format='sf',
            qfunc='Quit', ckey='', crit='pattern'):
        Pages.__init__(self)        # <- items, ilen, pages, itemsdict, cols
        self.name = name            # general name of an item
        if format in ('sf', 'bf'):  # available formats
            self.format = format    # key to format function
        else:
            raise TpagerError("the `%s' format is invalid." % format)
        self.qfunc = qfunc          # name of exit function
        if ckey and ckey in 'qQ-':
            raise TpagerError("the `%s' key is internally reserved." % ckey)
        else:
            self.ckey = ckey        # key to customize pager
        self.crit = crit            # criterion for customizing
        self.mcols = self.cols - 3  # available columms for menu
        self.header = ''

    def colTrunc(self, s, cols=0):
        '''Truncates string at beginning by inserting '>'
        if the string's width exceeds cols.'''
        if not cols:
            cols = self.mcols
        slen = len(s)
        if slen <= cols:
            return s
        else:
            return '>%s' % s[slen-cols:]

    def pageDisplay(self, menu, pn=1):
        '''Displays a page of items including header and choice menu.'''
        print self.header + self.pages[pn]
        return raw_input(self.colTrunc(menu))

    def interAct(self, newdict=True):
        '''Lets user page through a list of items and make a choice.'''
        retval = 0
        if newdict:
            Pages.pagesDict(self)
        self.header = '*%s*' % spl.sPl(self.ilen, self.name)
        self.header = '%s\n\n' % self.colTrunc(self.header, self.cols-2)
        plen = len(self.pages)
        if plen == 1: # no paging
            cs = ', ^C:Cancel'
            if self.ckey:
                cs = '%s, %s<%s>' % (cs, self.ckey, self.crit)
            if self.itemsdict:
                cs = '%s, Number' % cs
            menu = 'Page 1 of 1 [%s]%s ' % (self.qfunc, cs)
            reply = self.pageDisplay(menu)
            if reply:
                if reply in self.itemsdict:
                    retval = self.itemsdict[reply]
                elif self.ckey and reply.startswith(self.ckey):
                    retval = reply
                else:
                    self.interAct(newdict=False) # display same page
        else: # more than 1 page
            pn = 1 # start at first page
            pdir = -1 # initial paging direction reversed
            while True:
                bs = '' # reverse paging direction
                if 1 < pn < plen:
                    bs = '-:%s, ' % pds[pdir*-1]
                else:
                    pdir *= -1
                menu = 'Page %d of %d [%s], ^C:Cancel, %sq:%s' \
                    % (pn, plen, pds[pdir], bs, self.qfunc)
                if self.ckey:
                    menu = '%s, %s<%s>' % (menu, self.ckey, self.crit)
                menu = '%s, Number ' % menu
                reply = self.pageDisplay(menu, pn)
                if reply:
                    if reply in 'qQ':
                        break
                    elif reply in self.itemsdict:
                        retval = self.itemsdict[reply]
                        break
                    elif self.ckey and reply.startswith(self.ckey):
                        retval = reply
                        break
                    elif reply == '-' and bs:
                        pdir *= -1
                        pn = valclamp.valClamp(pn+pdir, 1, plen)
                    #else: same page displayed on invalid response
                else:
                    pn = valclamp.valClamp(pn+pdir, 1, plen)
        return retval
