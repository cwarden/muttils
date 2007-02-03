# $Id$

### configure defaults manually:
# /path/to/dir/containing/sigfiles
signaturedir = '~/.Sig'
# common suffix of signature files
suffix = '.sig'
###

from usage import Usage
from sigpager import Signature, SignatureError
import getopt, sys

# d: sigdir, f [prepend separator], h [help],
# s: defaultsig, t: sigtail

sigpager_help = '''
[-d <sigdir>][-f][-s <defaultsig>] \\
         [-t <sigtail>][-]
[-d <sigdir>][-f][-s <defaultsig>] \\
         [-t <sigtail>] <file> [<file> ...]
-h (display this help)'''

def userhelp(error=''):
    u = Usage(help=sigpager_help)
    u.printhelp(err=error)


def run():
    sigdir = signaturedir
    tail = suffix
    defsig = sigsep = inp = ''

    try:

        opts, args = getopt.getopt(sys.argv[1:], 'd:fhs:t:')
        for o, a in opts:
            if o == '-d':
                sigdir = a
            if o == '-f':
                sigsep = '-- \n'
            if o == '-h':
                userhelp()
            if o == '-s':
                defsig = a
            if o == '-t':
                tail = a
        if args == ['-']:
            inp = sys.stdin.read()
        else:
            targets = args

        s = Signature(sig=defsig, sdir=sigdir, sep=sigsep, tail=tail,
                inp=inp, targets=targets)
        s.underSign()

    except (getopt.GetoptError, SignatureError), e:
        userhelp(e)
