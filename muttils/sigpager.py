# $Id$

from tpager import Tpager, TpagerError
import os, random, re, readline, sys

class SignatureError(TpagerError):
    '''Exception class for Signature.'''

class Signature(Tpager):
    '''
    Provides functions to interactively choose a mail signature
    matched against a regular expression of your choice.
    '''
    def __init__(self,
            sig='', sdir='', sep='', tail='', inp='', targets=None):
        Tpager.__init__(self,
            name='sig', format='bf', qfunc='default sig', ckey='/')

        self.sig = sig or os.getenv('SIGNATURE') or '~/.signature'
        self.sig = os.path.expanduser(self.sig)
        if not self.sig or not os.path.isfile(self.sig):
            raise SignatureError('no default signature file found')
        self.sdir = os.path.expanduser(sdir)
        if not self.sdir or not os.path.isdir(self.sdir):
            raise SignatureError('no signature directory detected')

        self.tail = tail        # tail for sigfiles
        self.sep = sep          # sig including separator
        self.inp = inp          # append sig at input
        self.targets = []       # target files to sig
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
        except IOError, e:
            raise SignatureError('could not read %s; %s' % (fn, e))

    def getSig(self):
        if self.pat:
            self.items = filter(self.pat.search, self.sigs)
        else:
            self.items = self.sigs
        random.shuffle(self.items)
        try:
            return self.interAct()
        except TpagerError, e:
            raise SignatureError(e)

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
        sl = filter(lambda f: f.endswith(self.tail), os.listdir(self.sdir))
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
                try:
                    sig = self.sep
                    f = open(self.sig)
                    try:
                        sig += f.read()
                    finally:
                        f.close()
                except IOError, e:
                    raise SignatureError('could not read %s; %s'
                            % (self.sig, e))
            if not self.targets:
                sys.stdout.write(self.inp + sig)
            else:
                try:
                    for fn in self.targets:
                        f = open(fn, 'a')
                        try:
                            f.write(sig)
                        finally:
                            f.close()
                except IOError, e:
                    raise SignatureError('could not write to %s; %s' % (fn, e))
        elif self.inp:
            sys.stdout.write(self.inp)
        elif self.targets:
            sys.stdout.write('\n')
