sigpager_cset = '$Id$'

import os, random, re, readline, sys
from cheutils import readwrite
from tpager.Tpager import Tpager, TpagerError

# defaults:
sigdir = os.path.expanduser('~/.Sig')
defaultsig = os.getenv('SIGNATURE')
if not defaultsig:
    defaultsig = os.path.expanduser('~/.signature')
optstring = 'd:fhs:t:'
# d: sigdir, f [include separator], h [help],
# s: defaultsig, t: sigtail

sigpager_help = '''
[-d <sigdir>][-f][-s <defaultsig>] \\
         [-t <sigtail>][-]
[-d <sigdir>][-f][-s <defaultsig>] \\
         [-t <sigtail>] <file> [<file> ...]
-h (display this help)'''

def userHelp(error=''):
    from cheutils.usage import Usage
    u = Usage(help=sigpager_help, rcsid=sigpager_cset)
    u.printHelp(err=error)


class SignatureError(TpagerError):
    '''Exception class for Signature.'''

class Signature(Tpager):
    '''
    Provides functions to interactively choose a mail signature
    matched against a regular expression of your choice.
    '''
    def __init__(self):
        Tpager.__init__(self,
            name='sig', format='bf', qfunc='default sig', ckey='/')
        self.sig = defaultsig   # signature file
        self.sdir = sigdir      # directory containing sigfiles
        self.sigs = []          # complete list of signature strings
        self.tail = '.sig'      # tail for sigfiles
        self.sep = ''           # sig including separator
        self.inp = ''           # append sig at input
        self.targets = []       # target files to sig
        self.pat = None         # match sigs against pattern

    def argParser(self):
        import getopt
        try:
            opts, args = getopt.getopt(sys.argv[1:], optstring)
        except getopt.GetoptError, e:
            raise SignatureError(e)
        for o, a in opts:
            if o == '-d': self.sdir = a
            if o == '-f': self.sep = '-- \n'
            if o == '-h': userHelp()
            if o == '-s': self.sig = a
            if o == '-t': self.tail = a
        if args == ['-']:
            self.inp = sys.stdin.read()
        else:
            self.targets = args

    def getString(self, fn):
        sigfile = os.path.join(self.sdir, fn)
        return readwrite.readFile(sigfile)

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
                sig = self.sep + readwrite.readFile(self.sig)
            if not self.targets:
                sys.stdout.write(self.inp + sig)
            else:
                for targetfile in self.targets:
                    readwrite.writeFile(targetfile, sig, mode='a')
        elif self.inp:
            sys.stdout.write(self.inp)
        elif self.targets:
            sys.stdout.write('\n')


def run():
    try:
        siggi = Signature()
        siggi.argParser()
        siggi.underSign()
    except SignatureError, e:
        userHelp(e)
