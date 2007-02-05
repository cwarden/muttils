# $Id$

import pybrowser, ui, usage
import getopt, sys

pybrowser_help = '''
[<url>||<file> ...]
-t [<url>||<file> ...]   (%r)
-x [<url>||<file> ...]   (%r)
-h (display this help)'''

def userhelp(config, error=''):
    tb = config.get('browser', 'textbrowser')
    xb = config.get('browser', 'xbrowser')
    help = pybrowser_help % (tb, xb)
    usage.usage(help=help, err=error)


def run():
    '''Command interface to the Browser class.'''

    tb, xb = '', ''

    try:
        config = ui.config()

        opts, args = getopt.getopt(sys.argv[1:], 'htx')
        for o, a in opts:
            if o == '-h':
                userhelp(config)
            if o == '-t':
                tb = config.get('browser', 'textbrowser')
            if o == '-x':
                xb = config.get('browser', 'xbrowser')

        b = pybrowser.Browser(items=args, tb=tb, xb=xb,
                homeurl=config.get('browser', 'homepage'))
        b.urlVisit()

    except (getopt.GetoptError, ui.ConfigError, pybrowser.BrowserError), e:
        userhelp(config, error=e)
