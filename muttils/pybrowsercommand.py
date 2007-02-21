# $Id$

'''Launches browser to visit given urls (local and remote).
Completes short urls like "blacktrash.org" automagically.
Override choice of system default browser with option -b.
'''

import pybrowser
import util
import version
import optparse
import sys

proginfo = 'Pybrowser - python interface to system browsers'

def run():
    '''Runs the pybrowser script.'''
    parser = optparse.OptionParser(usage='%prog [option] [urls]',
            description=__doc__, version=version.version_(proginfo))
    parser.set_defaults(app='')
    parser.add_option('-b', '--browser', dest='app',
            help='prefer browser APP over system default')
    options, args = parser.parse_args()
    
    try:
        b = pybrowser.browser(items=args, app=options.app)
        parser.destroy()
        b.urlvisit()
    except util.DeadMan, inst:
        sys.exit(inst)
