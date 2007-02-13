# $Id$

###
# Caveat:
# If input is read from stdin, it should be of one type
# (text/plain, text/html, email) because the type detecting
# mechanism is only triggered once.
# However you should be able to run this on all kind of files,
# input is checked anew for each file.
###

import urlpager, version
from urlregex import valid_protos
import optparse, sys

proginfo = 'Urlpager - search, choose and retrieve url'

progdesc = '''Search files or standard input for urls,
choose 1 url interactively and retrieve it.
Urls are either web locations or Message-IDs.'''

def run():
    parser = optparse.OptionParser(formatter=optparse.TitledHelpFormatter(),
            usage='%prog [option] [files]', description=progdesc,
            version=version.version_(proginfo))
    parser.set_defaults(midrelax=False, specdirs=None,
            proto='all', pat=None, xb=False, tb=False, getdir='', ftp='',
            local=False, browse=False, news=False, mhiers=None, mspool=True)

    parser.add_option('-p', '--protocol', dest='proto',
            type='choice', choices=valid_protos,
            help='narrow down url choice to protocol PROTO')
    parser.add_option('-r', '--regex', dest='pat',
            help='narrow down url choice to urls matching PAT')
    parser.add_option('-x', '--xbrowser', dest='xb', action='store_true',
            help='prefer x11-browser')
    parser.add_option('-t', '--textbrowser', dest='tb', action='store_true',
            help='prefer textbrowser')
    parser.add_option('-w', '--wget', dest='getdir',
            help='download chosen url to directory GETDIR using wget')
    parser.add_option('-f', '--ftp',
            help='use ftp client FTP for ftp urls')
    parser.add_option('-i', '--midrelax', action='store_true',
            help='choose from undeclared message-ids (false positives probable)')
    parser.add_option('-l', '--local', action='store_true',
            help='search for chosen message only locally')
    parser.add_option('-b', '--browse', action='store_true',
            help='view chosen message at google groups with browser')
    parser.add_option('-n', '--news', action='store_true',
            help='news only: do not search local mailboxes')
    parser.add_option('-m', '--mbox', dest='kiosk',
            help='append message chosen by id to mbox KIOSK')
    parser.add_option('-d', '--dirs', dest='mhiers',
            help='search for message in directories MHIERS (colon-separated list, including mail spool)')
    parser.add_option('-D', '--specdirs',
            help='search for message in directories SPECDIRS (colon-separated list, excluding mail spool)')
    parser.add_option('-M', '--mask',
            help='exclude mailboxes matching MASK from search')

    options, args = parser.parse_args()

    for o in [options.midrelax, options.news, options.local, options.browse,
            options.kiosk, options.mhiers, options.specdirs, options.mask]:
        if o:
            options.proto = 'mid'
            break

    if options.midrelax:
        options.decl = False
    if options.specdirs:
        options.mhiers = options.specdirs
        options.mspool = False
    del options.midrelax, options.specdirs

    try:
        u = urlpager.urlpager(files=args, opts=options.__dict__)
        parser.destroy()
        u.urlsearch()
    except urlpager.UrlpagerError, inst:
        sys.exit(inst)
    except KeyboardInterrupt:
        sys.exit('need filenames or standard input')
