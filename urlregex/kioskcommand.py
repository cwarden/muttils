# $Id$

from urlregex.usage import Usage
from urlregex.kiosk import Kiosk, KioskError
from urlregex.Urlregex import Urlregex
import getopt, sys

### configure manually (mail_client defaults to "mail" if empty)
mail_client = 'mutt'
xbrowser = 'firefox'
textbrowser = 'w3m'
###

optstring = 'bd:D:hk:lM:ntx'

kiosk_help = '''
[-l][-d <mail hierarchy>[:<mail hierarchy> ...]] \\
        [-k <mbox>][-M <filemask>][-t] <ID> [<ID> ...]
[-l][-D <mail hierarchy>[:<mail hierarchy> ...]] \\
        [-k <mbox>][-M <filemask>][-t] <ID> [<ID> ...]
-n [-l][-k <mbox>][-t] <ID> [<ID> ...]
-b <ID> [<ID> ...]
-h (display this help)'''

def userhelp(error=''):
    u = Usage(help=kiosk_help)
    u.printhelp(err=error)


def run():
    '''Command interface to Kiosk.'''

    opts = {'mailer': mail_client}

    try:
        sysopts, args = getopt.getopt(sys.argv[1:], optstring)

        for o, a in sysopts:
            if o == '-b':
                opts['browse'] = True
                opts['mhiers'] = None
            if o == '-d': # specific mail hierarchies
                opts['mhiers'] = a.split(':')
            if o == '-D': # specific mail hierarchies, exclude mspool
                opts['mhiers'] = a.split(':')
                opts['mspool'] = False
            if o == '-h':
                userhelp()
            if o == '-l':
                opts['local'] = True
            if o == '-k':
                opts['kiosk'] = a
            if o == '-M':
                opts['mask'] = a
            if o == '-n':
                opts['mhiers'] = None # don't search local mailboxes
            if o == '-t':
                opts['tb'] = textbrowser
            if o == '-x':
                opts['xb'] = xbrowser
        u = Urlregex(proto='mid', uniq=False)
        u.findUrls(' '.join(args))
        if not u.items:
            userhelp('no valid Message-ID found')

        k = Kiosk(items=u.items, opts=opts)
        k.kioskStore()

    except (getopt.GetoptError, KioskError), e:
        userhelp(e)
    except KeyboardInterrupt:
        sys.exit('user cancelled')
