# $Id$

import tpager, util, ui
import os, random, re, readline, sys

class signature(tpager.tpager):
    '''
    Provides functions to interactively choose a mail signature
    matched against a regular expression of your choice.
    '''
    def __init__(self, parentui=None,
            dest=None, sig='', sdir='', sep='-- \n', tail=''):
        tpager.tpager.__init__(self,
            name='sig', format='bf', qfunc='default sig', ckey='/')
        self.ui = parentui or ui.config()
        self.ui.updateconfig()
        self.dest = dest        # input: list of files or string
        self.sig = (sig or self.ui.configitem('messages', 'signature')
                or os.getenv('SIGNATURE') or '~/.signature')
        self.sdir = sdir or self.ui.configitem('messages', 'sigdir')
        self.tail = tail or self.ui.configitem('messages', 'sigtail')
        self.sep = sep          # signature separator
        self.sigs = []          # complete list of signature strings
        self.pat = None         # match sigs against pattern

    def getstring(self, fn):
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
            raise util.DeadMan(inst)

    def getsig(self):
        if self.pat:
            self.items = filter(self.pat.search, self.sigs)
        else:
            self.items = self.sigs
        random.shuffle(self.items)
        return self.interact()

    def checkpattern(self):
        try:
            self.pat = re.compile(r'%s' % self.pat, re.I)
        except re.error, inst:
            sys.stdout.write('%s in pattern %s\n' % (inst, self.pat))
            prompt = ('[choose from %d signatures], new pattern: '
                    % len(self.sigs))
            try:
                self.pat = raw_input(prompt) or None
            except KeyboardInterrupt:
                self.pat = None
            if self.pat:
                self.checkpattern()

    def sign(self):
        self.sdir = util.absolutepath(self.sdir)
        try:
            sl = filter(lambda f: f.endswith(self.tail), os.listdir(self.sdir))
        except OSError, inst:
            raise util.DeadMan(inst)
        if not sl:
            raise util.DeadMan('no signature files in %s' % self.sdir)
        self.sigs = [self.getstring(fn) for fn in sl]
        while True:
            reply = self.getsig()
            if reply and reply.startswith(self.ckey):
                self.pat = reply[1:]
                self.checkpattern()
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
                    raise util.DeadMan(inst)
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
                    raise util.DeadMan(inst)
        elif self.dest:
            sys.stdout.write('\n')
