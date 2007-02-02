kiosk_cset = '$Id$'

from kiosk import Kiosk, KioskError
from Urlregex import Urlregex
import getopt, sys

### configure manually (mail_client defaults to "mail" if empty)
mail_client = 'mutt'
xbrowser = 'firefox'
textbrowser = 'w3m'
###

kiosk_help = '''
[-l][-d <mail hierarchy>[:<mail hierarchy> ...]] \\
        [-k <mbox>][-M <filemask>][-t] <ID> [<ID> ...]
[-l][-D <mail hierarchy>[:<mail hierarchy> ...]] \\
        [-k <mbox>][-M <filemask>][-t] <ID> [<ID> ...]
-n [-l][-k <mbox>][-t] <ID> [<ID> ...]
-b <ID> [<ID> ...]
-h (display this help)'''

def userHelp(error=''):
    from cheutils.usage import Usage
    u = Usage(help=kiosk_help, rcsid=kiosk_cset)
    u.printHelp(err=error)


def run():
    '''Command interface to Kiosk.'''

    optstr = 'bd:D:hk:lM:ntx'

    opts = {'mailer': mail_client}

    try:
        sysopts, args = getopt.getopt(sys.argv[1:], optstr)

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
                userHelp()
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
            userHelp('no valid Message-ID found')

        k = Kiosk(items=u.items, opts=opts)
        k.kioskStore()

    except (getopt.GetoptError, KioskError), e:
        userHelp(e)
    except KeyboardInterrupt:
        sys.exit('user cancelled')
