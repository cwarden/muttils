# $Id$

import sigpager
import version
import optparse
import sys

proginfo = 'Sigpager - email signature selection'

def run():
    parser = optparse.OptionParser(usage='%prog [options] [files to sign]',
            version=version.version_(proginfo))
    parser.set_defaults(defsig='', sigdir='~/.Sig', defsig='',
            tail='.sig', sigsep='-- \n')

    parser.add_option('-d', '--sigdir',
            help='choose from signatures in directory SIGDIR')
    parser.add_option('-s', '--defsig',
            help='default signature from file DEFSIG')
    parser.add_option('-t', '--tail',
            help='signatures are read from files with suffix TAIL')
    parser.add_option('-S', '--nosep',
            dest='sigsep', action='store_const', const= '',
            help='suppress prepending of signature separator')

    options, args = parser.parse_args()

    try:
        s = sigpager.signature(dest=args,
                sig=options.defsig, sdir=options.sigdir,
                tail=options.tail, sep=options.sigsep)
        s.sign()
    except sigpager.SignatureError, inst:
        sys.exit(inst)
