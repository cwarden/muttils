# $Id$

###
# Caveat:
# If input is read from stdin, it should be of one type
# (text/plain, text/html, email) because the type detecting
# mechanism is only triggered once.
# However you should be able to run this on all kind of files,
# input is checked anew for each file.
###

'''Searches files or standard input for urls, and retrieves them.
Urls are either web locations or Message-IDs.

Valid url schemes are: "web", "http", "ftp", "mid" (for Message-ID).

Options "-p mid", "-i", "-n", "-B", "-l", "-m", "-d", "-D", "-M"
switch to message retrieval.
'''

import urlbatcher, util, version
import optparse, sys

valid_protos = ['web', 'http', 'ftp', 'mid']

proginfo = 'Urlbatcher - search and retrieve urls'

def run():
    '''Runs the urlbatcher script.'''
    parser = optparse.OptionParser(formatter=optparse.TitledHelpFormatter(),
                                   usage='%prog [options] [files]',
                                   description=__doc__,
                                   version=version.version_(proginfo))
    parser.set_defaults(proto='web', pat=None, app='', getdir='',
                        midrelax=False, local=False, browse=False, news=False,
                        kiosk='', mhiers='', specdirs='', mask=None)

    parser.add_option('-p', '--protocol', dest='proto',
                      type='choice', choices=valid_protos,
                      help='narrow down url choice to protocol PROTO')
    parser.add_option('-r', '--regex', dest='pat',
                      help='narrow down url choice to urls matching PAT')
    parser.add_option('-b', '--browser', dest='app',
                      help='prefer browser APP over $BROWSER environment')
    parser.add_option('-w', '--wget', dest='getdir',
                      help='download urls to directory GETDIR using wget')
    parser.add_option('-i', '--midrelax', action='store_true',
                      help='choose from undeclared message-ids '
                           '(false positives probable)')
    parser.add_option('-l', '--local', action='store_true',
                      help='search for messages only locally')
    parser.add_option('-B', '--browse', action='store_true',
                      help='view messages at google groups with browser')
    parser.add_option('-n', '--news', action='store_true',
                      help='news only: do not search local mailboxes')
    parser.add_option('-m', '--mbox', dest='kiosk',
                      help='append messages to mbox KIOSK')
    parser.add_option('-d', '--dirs', dest='mhiers',
                      help='search for messages in directories MHIERS '
                           '(colon-separated list, including mail spool)')
    parser.add_option('-D', '--specdirs',
                      help='search for messages in directories SPECDIRS '
                           '(colon-separated list, excluding mail spool)')
    parser.add_option('-M', '--mask',
                      help='exclude mailboxes matching MASK from search')

    options, args = parser.parse_args()

    try:
        u = urlbatcher.urlbatcher(files=args, opts=options.__dict__)
        parser.destroy()
        u.urlsearch()
    except (util.DeadMan, IOError, KeyboardInterrupt), inst:
        sys.exit(inst)
