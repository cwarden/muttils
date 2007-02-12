# $Id$

import pybrowser
import version
import optparse
import sys

proginfo = 'Pybrowser - python interface to system browsers'

def run():
    parser = optparse.OptionParser(usage='%prog [option] [urls]',
            version=version.version_(proginfo))
    parser.set_defaults(xbrowser=False, textbrowser=False)

    parser.add_option('-x', '--xbrowser', action='store_true',
            help='prefer x11-browser')
    parser.add_option('-t', '--textbrowser', action='store_true',
            help='prefer textbrowser')

    options, args = parser.parse_args()
    
    try:
        b = pybrowser.browser(items=args,
                tb=options.textbrowser, xb=options.xbrowser)
        b.urlvisit()
    except pybrowser.BrowserError, inst:
        sys.exit(inst)
