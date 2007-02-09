# $Id$

import os, sys

class termplus(object):
    '''
    Provides readline and write methods
    for an interactive terminal device.
    '''
    def __init__(self):
        self.dev = os.ctermid()

    def write(self, o):
        f = open(self.dev, 'wb')
        try:
            f.write(o)
        finally:
            f.close()
    
    def readline(self, size=-1):
        s = ''
        f = open(self.dev, 'rb')
        try:
            s = f.readline(size)
        finally:
            f.close()
        return s

    def flush(self):
        pass


class iterm(termplus):
    '''
    Provides interactive terminal devices.
    '''
    def __init__(self):
        termplus.__init__(self)
        self.iostack = []

    def terminit(self):
        self.iostack.append((sys.stdin, sys.stdout))
        sys.stdin, sys.stdout = self, self

    def reinit(self):
        '''Switches back to previous term.'''
        try:
            sys.stdin, sys.stdout = self.iostack.pop()
        except IndexError:
            # if stack was empty eg. because of KeyboardInterrupt
            # do not raise an Error
            pass
