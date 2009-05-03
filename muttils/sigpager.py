# $Id$

from muttils import tpager, util, ui
import os, random, re
try:
    import readline
except ImportError:
    pass

class signature(tpager.tpager):
    '''
    Provides functions to interactively choose a mail signature
    matched against a regular expression of your choice.
    '''
    sigs = [] # complete list of signature strings

    def __init__(self, parentui=None,
                 dest=None, sig='', sdir='', sep='-- \n', tail=''):
        self.ui = parentui or ui.ui()
        tpager.tpager.__init__(self, self.ui, name='sig',
                               format='bf', qfunc='default sig', ckey='/')
        self.ui.updateconfig()
        self.dest = dest        # input: list of files or string
        self.sig = (sig or self.ui.configitem('messages', 'signature')
                    or os.getenv('SIGNATURE') or '~/.signature')
        self.sdir = sdir or self.ui.configitem('messages', 'sigdir')
        self.tail = tail or self.ui.configitem('messages', 'sigtail')
        self.sep = sep          # signature separator

    def getstring(self, fn):
        fn = os.path.join(self.sdir, fn)
        f = open(fn)
        try:
            s = f.read()
        finally:
            f.close()
        return s

    def getsig(self, weed_re=None):
        if weed_re:
            self.items = [sig for sig in self.sigs if weed_re.search(sig)]
        else:
            self.items = self.sigs
        random.shuffle(self.items)
        return self.interact()

    def checkpattern(self, pat):
        try:
            return re.compile(r'%s' % pat, re.UNICODE|re.IGNORECASE)
        except re.error, inst:
            self.ui.warn('%s in pattern %s\n' % (inst, pat))
            prompt = ('[choose from %d signatures], new pattern: '
                    % len(self.sigs))
            try:
                pat = raw_input(prompt)
            except KeyboardInterrupt:
                pat = ''
            if pat:
                return self.checkpattern(pat)

    def sign(self):
        self.sdir = util.absolutepath(self.sdir)
        sl = [f for f in os.listdir(self.sdir) if f.endswith(self.tail)]
        if not sl:
            raise util.DeadMan('no signature files in %s' % self.sdir)
        self.sigs = [self.getstring(fn) for fn in sl]
        weed_re = None
        while True:
            reply = self.getsig(weed_re)
            if reply.startswith(self.ckey):
                weed_re = self.checkpattern(reply[1:])
            else:
                break
        if self.items is not None:
            if self.items:
                sig = self.sep + self.items[0]
            else:
                self.sig = util.absolutepath(self.sig)
                f = open(self.sig)
                try:
                    sig = self.sep + f.read()
                finally:
                    f.close()
            if not self.dest:
                self.ui.write(sig)
            else:
                for fn in self.dest:
                    f = open(fn, 'a')
                    try:
                        f.write(sig)
                    finally:
                        f.close()
        elif self.dest:
            self.ui.write('\n')
