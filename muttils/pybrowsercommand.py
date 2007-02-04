# $Id$

### configure manually:
tbrowser = 'w3m'
xbrowser = 'firefox'
homeurl  = 'http://localhost/mercurial'
###

import pybrowser, usage
import getopt, sys

pybrowser_help = '''
[<url>||<file> ...]
-t [<url>||<file> ...]   (%s)
-x [<url>||<file> ...]   (%s)
-h (display this help)''' % (tbrowser, xbrowser)

def userHelp(error=''):
    usage.usage(help=pybrowser_help, err=error)


def run():
    '''Command interface to the Browser class.'''

    tb, xb = '', ''

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'htx')
        for o, a in opts:
            if o == '-h':
                userHelp()
            if o == '-t':
                tb = tbrowser
            if o == '-x':
                xb = xbrowser
        b = pybrowser.Browser(items=args, tb=tb, xb=xb, homeurl=homeurl)
        b.urlVisit()
    except (getopt.GetoptError, pybrowser.BrowserError), e:
        userHelp(e)
