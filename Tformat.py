# $Id$

class TformatError(Exception):
    '''Exception class for Tformat.'''

class Tformat(object):
    '''
    Subclass to Pages (<- format, itemsdict, keys).
    Provides formatting methods
    for interactive terminal.
    '''
    def __init__(self, format='sf'):
        self.format = format # sf: simple format, bf: bracket format
        self.itemsdict = {}  # dictionary of items to choose
        self.keys = []       # itemsdict's keys
        self.maxl = 0        # length of last key

    def simpleFormat(self, key):
        '''Simple format of choice menu,
        recommended for 1 line items.'''
        return '%s) %s\n' % (key.rjust(self.maxl), self.itemsdict[key])

    def bracketFormat(self, key):
        '''Format of choice menu with items
        that are longer than 1 line.'''
        return '[%s]\n%s\n' % (key, self.itemsdict[key])

    def formatItems(self):
        formdict = {'sf': self.simpleFormat, 'bf': self.bracketFormat}
        if self.format not in formdict:
            raise TformatError("`%s': invalid format, use one of `sf', `bf'"
                    % self.format)
        if not self.keys:
            return []
        # dictionary of format functions
        if self.format == 'sf':
            self.maxl = len(self.keys[-1])
        formatfunc = formdict[self.format]
        return [formatfunc(key) for key in self.keys]
