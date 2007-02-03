# $Id$

###
# Caveat:
# If input is read from stdin, it should be of one type
# (text/plain, text/html, email) because the type detecting
# mechanism is only triggered once.
# However you should be able to run this on all kind of files,
# input is checked anew for each file.
###

import urlregex.util
from urlregex.usage import Usage
from urlregex.urlbatcher import Urlbatcher, UrlbatcherError
import getopt, os.path, sys

### configure manually
### mail_client must be one of: mail, mutt, muttng,
### and defaults to mail if empty
mail_client = 'mutt'
xbrowser = 'firefox'
###

optstring = 'd:D:hiIk:lnr:w:x'

urlbatcher_help = '''
[-x][-r <pattern>][file ...]
-w <download dir> [-r <pattern]
-i [-r <pattern>][-k <mbox>][<file> ...]
-I [-r <pattern>][-k <mbox>][<file> ...]
-l [-I][-r <pattern>][-k <mbox>][<file> ...]
-d <mail hierarchy>[:<mail hierarchy>[:...]] \\
        [-l][-I][-r <pattern>][-k <mbox>][<file> ...] 
-D <mail hierarchy>[:<mail hierarchy>[:...]] \\
        [-l][-I][-r <pattern>][-k <mbox>][<file> ...]
-n [-l][-I][-r <pattern>][-k <mbox>][<file> ...] 
-h (display this help)'''

def userhelp(error='', i=False):
    u = Usage(help=urlbatcher_help)
    u.printhelp(err=error, interrupt=i)


def run():
    '''Command interface to Urlbatcher.'''

    opts = {'mailer': mail_client}

    try:
        sysopts, opts['files'] = getopt.getopt(sys.argv[1:], optstring)

        for o, a in sysopts:
            if o == '-d': # specific mail hierarchies
                opts['proto'] = 'mid'
                opts['mhiers'] = a.split(':')
            if o == '-D': # specific mail hierarchies, exclude mspool
                opts['proto'] = 'mid'
                opts['mspool'] = False
                opts['mhiers'] = a.split(':')
            if o == '-h':
                userhelp()
            if o == '-i': # look for message-ids
                opts['proto'] = 'mid'
            if o == '-I': # look for declared message-ids
                opts['proto'] = 'mid'
                opts['decl'] = True
            if o == '-k': # mailbox to store retrieved messages
                opts['proto'] = 'mid'
                opts['kiosk'] = a
            if o == '-l': # only local search for message-ids
                opts['proto'] = 'mid'
                opts['local'] = True
            if o == '-n': # don't search local mailboxes
                opts['proto'] = 'mid'
                opts['mhiers'] = None
            if o == '-r':
                opts['pat'] = a
            if o == '-w': # download dir for wget
                if not os.path.isdir(urlregex.util.absolutepath(a)):
                    userhelp('%s: not a directory' % a)
                opts['proto'] = 'web'
            if o == '-x':
                opts['xb'] = xbrowser

        u = Urlbatcher(opts=opts)
        u.urlSearch()

    except (getopt.GetoptError, UrlbatcherError), e:
        userhelp(e)
    except KeyboardInterrupt:
        userhelp('needs filename(s) or stdin', i=True)
