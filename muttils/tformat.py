# $Id$

import util

class tformat(object):
    '''
    Subclass to ipages (<- format, itemsdict, keys).
    Provides formatting methods
    for interactive terminal.
    '''
    def __init__(self, items=None, format='sf'):
        self.format = format     # sf: simple format, bf: bracket format
        self.items = items or [] # (text) items to choose from
        self.itemsdict = {}      # dictionary of items to choose
        self.ilen = 0            # length of items' list

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
