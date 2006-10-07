sigpager_cset = '$Hg: sigpager.py,v$'

import os, random, re, readline
from cheutils import readwrite
from LastExit import LastExit
from Tpager import Tpager

# defaults:
sigdir = os.path.expanduser('~/.Sig')
defaultsig = os.getenv('SIGNATURE')
if not defaultsig:
    defaultsig = os.path.expanduser('~/.signature')
optstring = 'd:fhs:t:w'
# d: sigdir, f [include separator], h [help],
# s: defaultsig, t: sigtail, w [(over)write target file(s)]

sigpager_help = '''
[-d <sigdir>][-f][-s <defaultsig>] \\
         [-t <sigtail>][-]
[-d <sigdir>][-f][-s <defaultsig>] \\
         [-t <sigtail>][-w] <file> [<file> ...]
-h (display this help)'''

def userHelp(error=''):
    from cheutils import exnam
    u = exnam.Usage(help=sigpager_help, rcsid=sigpager_cset)
    u.printHelp(err=error)


class Signature(Tpager, LastExit):
    '''
    Provides functions to interactively choose a mail signature
    matched against a regular expression of your choice.
    '''
    def __init__(self):
        Tpager.__init__(self,   # <- item, name, format, qfunc
            name='sig', format='bf', qfunc='default sig, C-c:cancel', ckey='/')
        LastExit.__init__(self)
        self.sign = ''          # chosen self.signature
        self.sig = defaultsig   # self.signature file
        self.sdir = sigdir      # directory containing sigfiles
        self.tail = '.sig'      # tail for sigfiles
        self.full = False       # sig including separator
        self.inp = ''           # append sig at input
        self.targets = []       # target files to self.sign
        self.w = 'wa'           # if 'w': overwrite target file(s)
                                # sig appended otherwise
        self.pat = None         # match sigs against pattern

    def argParser(self):
        import getopt, sys
        try:
            opts, args = getopt.getopt(sys.argv[1:], optstring)
        except getopt.GetoptError, e:
            userHelp(e)
        for o, a in opts:
            if o == '-d': self.sdir = a
            if o == '-f': self.full = True
            if o == '-h': userHelp()
            if o == '-s': self.sig = a
            if o == '-t': self.tail = a
            if o == '-w': self.w = 'w'
        if args == ['-']:
            self.inp = sys.stdin.read()
        else:
            self.targets = args

    def getString(self, fn):
        sigfile = os.path.join(self.sdir, fn)
        return readwrite.readFile(sigfile)

    def getSig(self):
        siglist = filter(lambda f: f.endswith(self.tail),
                os.listdir(self.sdir) )
        if siglist:
            random.shuffle(siglist)
            self.items = [self.getString(fn) for fn in siglist]
            if self.pat and self.items:
                self.items = filter(lambda i: self.pat.search(i), self.items)
            try:
                self.sign = Tpager.interAct(self)
            except KeyboardInterrupt:
                self.sign = None

    def checkPattern(self):
        try:
            self.pat = re.compile(r'%s' % self.pat, re.I)
        except re.error, e:
            print '%s in pattern %s' % (e, self.pat)
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

    def siggiLoop(self):
        while 1:
            self.getSig()
            if self.sign and self.sign.startswith(self.ckey):
                self.pat = self.sign[1:]
                self.sign = ''
                self.checkPattern()
                Tpager.__init__(self,
                    self.name, self.format, self.qfunc, self.ckey)
            else:
                break

    def underSign(self):
        if not self.targets:
            LastExit.termInit(self)
        self.siggiLoop()
        if not self.targets:
            LastExit.reInit(self)
        if self.sign != None:
            if not self.sign:
                self.sign = readwrite.readFile(self.sig)
            if self.full:
                self.sign = '-- \n%s' % self.sign
            self.sign = self.sign.rstrip() # get rid of EOFnewline
            if not self.targets:
                if not self.inp:
                    print self.sign
                else:
                    print '%s%s' % (self.inp, self.sign)
            else:
                for targetfile in self.targets:
                    readwrite.writeFile(targetfile, self.sign, self.w)
        elif self.inp:
            print self.inp
        elif self.targets:
            print


def run():
    siggi = Signature()
    siggi.argParser()
    siggi.underSign()
