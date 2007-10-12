# $Id$

import os, sys

class termplus(object):
    '''
    Provides readline and write methods
    for an interactive terminal device.
    '''
    def __init__(self):
        cterm = os.ctermid()
        self.stdin = open(cterm, 'rb')
        self.stdout = open(cterm, 'wb')

    def write(self, s):
        try:
            self.stdout.write(s)
        finally:
            self.close()

    def readline(self, size=-1):
        try:
            return self.stdin.readline(size)
        finally:
            self.close()

    def flush(self):
        self.stdout.flush()

    def close(self):
        self.stdin.close()
        self.stdout.close()


class iterm(termplus):
    '''
    Provides interactive terminal devices.
    '''
    def __init__(self):
        termplus.__init__(self)
        self.iostack = []

    def terminit(self):
        self.iostack.append((sys.stdin, sys.stdout))
        sys.stdin, sys.stdout = self.stdin, self.stdout

    def reinit(self):
        '''Switches back to previous term.'''
        try:
            sys.stdin, sys.stdout = self.iostack.pop()
        except IndexError:
            # if stack was empty eg. because of KeyboardInterrupt
            # do not raise an Error
            pass
