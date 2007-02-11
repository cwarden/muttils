# $Id$

import util
from tpager import Tpager, TpagerError
import os, random, re, readline, sys

class SignatureError(Exception):
    '''Exception class for Signature.'''
    def __init__(self, inst=''):
        self.inst = inst
    def __str__(self):
        if isinstance(self.inst, str):
            return self.inst
        return str(self.inst)

class Signature(Tpager):
    '''
    Provides functions to interactively choose a mail signature
    matched against a regular expression of your choice.
    '''
    def __init__(self, dest=None, sig='', sdir='', sep='-- \n', tail=''):
        Tpager.__init__(self,
            name='sig', format='bf', qfunc='default sig', ckey='/')
        self.dest = dest        # input: list of files or string
        self.sig = sig or os.getenv('SIGNATURE') or '~/.signature'
        self.sdir = sdir        # directory containing sig files
        self.tail = tail        # suffix of signature files
        self.sep = sep          # signature separator
        self.sigs = []          # complete list of signature strings
        self.pat = None         # match sigs against pattern

    def getString(self, fn):
        fn = os.path.join(self.sdir, fn)
        s = ''
        try:
            f = open(fn)
            try:
                s = f.read()
            finally:
                f.close()
            return s
        except IOError, inst:
            raise SignatureError(inst)

    def getSig(self):
        if self.pat:
            self.items = filter(self.pat.search, self.sigs)
        else:
            self.items = self.sigs
        random.shuffle(self.items)
        try:
            return self.interAct()
        except TpagerError, inst:
            raise SignatureError(inst)

    def checkPattern(self):
        try:
            self.pat = re.compile(r'%s' % self.pat, re.I)
        except re.error, e:
            sys.stdout.write('%s in pattern %s\n' % (e, self.pat))
            self.pat = None
            self.getPattern()

    def getPattern(self):
        prompt = 'C-c to cancel or\n' \
            'Enter pattern to match signatures against:\n'
        try:
            self.pat = raw_input(prompt)
        except KeyboardInterrupt:
            self.pat = None
        if self.pat:
            self.checkPattern()

    def underSign(self):
        self.sdir = util.absolutepath(self.sdir)
        try:
            sl = filter(lambda f: f.endswith(self.tail), os.listdir(self.sdir))
        except OSError, inst:
            raise SignatureError(inst)
        if not sl:
            raise SignatureError('no signature files in %s' % self.sdir)
        self.sigs = [self.getString(fn) for fn in sl]
        while True:
            reply = self.getSig()
            if reply and reply.startswith(self.ckey):
                self.pat = reply[1:]
                self.checkPattern()
            else:
                break
        if self.items is not None:
            if self.items:
                sig = self.sep + self.items[0]
            else:
                self.sig = util.absolutepath(self.sig)
                try:
                    f = open(self.sig)
                    try:
                        sig = self.sep + f.read()
                    finally:
                        f.close()
                except IOError, inst:
                    raise SignatureError(inst)
            if not self.dest:
                sys.stdout.write(sig)
            else:
                try:
                    for fn in self.dest:
                        f = open(fn, 'a')
                        try:
                            f.write(sig)
                        finally:
                            f.close()
                except IOError, inst:
                    raise SignatureError(inst)
        elif self.dest:
            sys.stdout.write('\n')
