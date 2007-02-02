urlpager_cset = '$Id$'

###
# Caveat:
# If input is read from stdin, it should be of one type
# (text/plain, text/html, email) because the type detecting
# mechanism is only triggered once.
# However you should be able to run this on all kind of files,
# input is checked anew for each file.
###

import util
from urlpager import Urlpager, UrlpagerError
import getopt, os.path, sys

### configure manually (mail_client defaults to "mail" if empty)
mail_client = 'mutt'
xbrowser = 'firefox'
textbrowser = 'w3m'
###

optstring = 'bd:D:f:hiIlM:np:k:r:tw:x'

urlpager_help = '''
[-p <protocol>][-r <pattern>][-t][-x][-f <ftp client>][<file> ...]
-w <download dir> [-r <pattern]
-i [-M <filemask>][-r <pattern>][-k <mbox>][<file> ...]
-I [-M <filemask>][-r <pattern>][-k <mbox>][<file> ...]
-l [-I][-M <filemask>][-r <pattern>][-k <mbox>][<file> ...]
-d <mail hierarchy>[:<mail hierarchy>[:...]] \\
        [-I][-l][-M <filemask>][-r <pattern>][-k <mbox>][<file> ...]
-D <mail hierarchy>[:<mail hierarchy>[:...]] \\
        [-I][-l][-M <filemask>][-r <pattern>][-k <mbox>][<file> ...]
-n [-r <pattern][-I][-l][-k <mbox>][<file> ...]
-b [-r <pattern][-I][<file> ...]
-h (display this help)'''

def userHelp(error='', i=False):
    from cheutils.usage import Usage
    u = Usage(help=urlpager_help, rcsid=urlpager_cset)
    u.printHelp(err=error, interrupt=i)


def run():
    '''Command interface to Urlpager.'''

    opts = {'mailer': mail_client}

    try:
        sysopts, opts['files'] = getopt.getopt(sys.argv[1:], optstring)

        for o, a in sysopts:
            if o == '-b': # don't look up msgs locally
                opts['proto'] = 'mid'
                opts['browse'] = True
            if o == '-d': # specific mail hierarchies
                opts['proto'] = 'mid'
                opts['mhiers'] = a.split(':')
            if o == '-D': # specific mail hierarchies, exclude mspool
                opts['proto'] = 'mid'
                opts['mspool'] = False
                opts['mhiers'] = a.split(':')
            if o == '-f': # ftp client
                opts['ftp'] = a
            if o == '-h':
                userHelp()
            if o == '-I': # look for declared message-ids
                opts['proto'] = 'mid'
                opts['decl'] = True
            if o == '-i': # look for ids, in text w/o prot (email false positives)
                opts['proto'] = 'mid'
            if o == '-k': # mailbox to store retrieved message
                opts['proto'] = 'mid'
                opts['kiosk'] = a
            if o == '-l': # only local search for message-ids
                opts['proto'] = 'mid'
                opts['local'] = True
            if o == '-M': # file mask
                opts['proto'] = 'mid'
                opts['mask'] = a
            if o == '-n': # don't search mailboxes for message-ids
                opts['proto'] = 'mid'
                opts['mhiers'] = None
            if o == '-p': # protocol(s)
                opts['proto'] = a
            if o == '-r': # regex pattern to match urls against
                opts['pat'] = a
            if o == '-x': # xbrowser
                opts['xb'] = xbrowser
            if o == '-t': # text browser command
                opts['tb'] = textbrowser
            if o == '-w': # download dir for wget
                if not os.path.isdir(util.absolutepath(a)):
                    userHelp('%s: not a directory' % a)
                opts['proto'] = 'web'
                opts['getdir'] = a

        u = Urlpager(opts=opts)
        u.urlSearch()

    except (getopt.GetoptError, UrlpagerError), e:
        userHelp(e)
    except KeyboardInterrupt:
        userHelp('needs filename(s) or stdin', i=True)
