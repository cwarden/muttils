# $Id$

'''Displays html message read from stdin.

$BROWSER environment may be overridden with option "-b".
'''

from muttils import viewhtmlmsg, util
import optparse, sys

proginfo = 'Viewhtmlmsg - view html message in browser'

def run():
    '''Runs the viewhtmlmsg script.'''
    parser = optparse.OptionParser(usage='%prog [options]',
                                   description=__doc__,
                                   version=util.fullversion(proginfo))
    parser.set_defaults(safe=False, keep=None, app='')
    parser.add_option('-s', '--safe', action='store_true',
                      help='view html w/o loading remote files')
    parser.add_option('-k', '--keep', type='int',
                      help='remove temporary files after KEEP seconds '
                           '(0 for keeping files)')
    parser.add_option('-b', '--browser', dest='app',
                      help='prefer browser APP over $BROWSER environment')
    
    options, args = parser.parse_args()
    del parser

    try:
        v = viewhtmlmsg.viewhtml(inp=args, safe=options.safe,
                                 keep=options.keep, app=options.app)
        v.view()
    except (util.DeadMan, IOError, KeyboardInterrupt), inst:
        sys.exit(inst)
