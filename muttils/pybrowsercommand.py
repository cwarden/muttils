# $Id$

'''Launches browser to visit given urls (local and remote).

Completes short urls like "blacktrash.org" automagically.

$BROWSER environment may be overridden with option "-b".
'''

import optparse, sys
from muttils import pybrowser, util

proginfo = 'Pybrowser - python interface to system browsers'

def run():
    '''Runs the pybrowser script.'''
    parser = optparse.OptionParser(usage='%prog [option] [urls]',
                                   description=__doc__,
                                   version=util.fullversion(proginfo))
    parser.set_defaults(app='')
    parser.add_option('-b', '--browser', dest='app',
                      help='prefer browser APP over $BROWSER environment')
    options, args = parser.parse_args()
    del parser

    try:
        b = pybrowser.browser(items=args, app=options.app, evalurl=True)
        b.urlvisit()
    except util.DeadMan, inst:
        sys.exit(inst)
