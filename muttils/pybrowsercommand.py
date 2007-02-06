# $Id$

import pybrowser, usage
import getopt, sys

pybrowser_help = '''
[<url>||<file> ...]
-t [<url>||<file> ...]
-x [<url>||<file> ...]
-h (display this help)'''

def userhelp(error=''):
    usage.usage(help=pybrowser_help, err=error)


def run():
    '''Command interface to the Browser class.'''

    tb, xb = False, False

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'htx')
        for o, a in opts:
            if o == '-h':
                userhelp()
            if o == '-t':
                tb = True
            if o == '-x':
                xb = True

        b = pybrowser.Browser(items=args, tb=tb, xb=xb)
        b.urlVisit()

    except (getopt.GetoptError, pybrowser.BrowserError), e:
        userhelp(error=e)
