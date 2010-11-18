'''Presents choice of randomly ordered email signatures
and prints selected signature to standard output or files.
'''

# $Id$

from muttils import sigpager, util
import optparse, sys

proginfo = 'Sigpager - email signature selection'

def run():
    '''Runs the sigpager script.'''
    parser = optparse.OptionParser(usage='%prog [options] [files to sign]',
                                   description=__doc__,
                                   version=util.fullversion(proginfo))
    parser.set_defaults(defsig='', sigdir='', tail='', sigsep='-- \n')

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
    del parser

    try:
        s = sigpager.signature(options.defsig, options.sigdir, options.tail,
                               options.sigsep, args)
        s.sign()
    except (util.DeadMan, IOError, OSError), inst:
        sys.exit(inst)
