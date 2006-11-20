urlbatcher_cset = '$Hg: urlbatcher.py,v$'

###
# Caveat:
# If input is read from stdin, it should be of one type
# (text/plain, text/html, email) because the type detecting
# mechanism is only triggered once.
# However you should be able to run this on all kind of files,
# input is checked anew for each file.
###

from Urlcollector import Urlcollector, UrlcollectorError
from kiosk import Kiosk, KioskError
from tpager.LastExit import LastExit
from cheutils import spl, systemcall

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

def userHelp(error=''):
    from cheutils.usage import Usage
    u = Usage(help=urlbatcher_help, rcsid=urlbatcher_cset)
    u.printHelp(err=error)

def goOnline():
    try:
        from cheutils import conny
        conny.appleConnect()
    except ImportError:
        pass

class UrlbatcherError(Exception):
    '''Exception class for the urlbatcher module.'''

class Urlbatcher(Urlcollector, Kiosk, LastExit):
    '''
    Parses input for either web urls or message-ids.
    Browses all urls or creates a message tree in mutt.
    You can specify urls/ids by a regex pattern.
    '''
    def __init__(self):
        Kiosk.__init__(self)        # <- kiosk, mhiers, mspool, local, google, xb, tb
        LastExit.__init__(self)
        Urlcollector.__init__(self, proto='web') # <- (Urlregex) proto, decl, items, files, pat
        self.getdir = ''            # download in dir via wget

    def argParser(self):
        import getopt, sys
        try:
            opts, self.files = getopt.getopt(sys.argv[1:], optstring)
        except getopt.GetoptError, e:
            raise UrlbatcherError(e)
        for o, a in opts:
            if o == '-d': # specific mail hierarchies
                self.proto = 'mid'
                self.mhiers = a.split(':')
            if o == '-D': # specific mail hierarchies, exclude mspool
                self.proto = 'mid'
                self.mspool = False
                self.mhiers = a.split(':')
            if o == '-h':
                userHelp()
            if o == '-i': # look for message-ids
                self.proto = 'mid'
            if o == '-I': # look for declared message-ids
                self.proto = 'mid'
                self.decl = True
            if o == '-k': # mailbox to store retrieved messages
                self.proto = 'mid'
                self.kiosk = a
            if o == '-l': # only local search for message-ids
                self.proto = 'mid'
                self.local = True
            if o == '-n': # don't search local mailboxes
                self.proto = 'mid'
                self.mhiers = None
            if o == '-r':
                self.pat = a
            if o == '-w': # download dir for wget
                from cheutils import filecheck
                getdir = a
                self.getdir = filecheck.fileCheck(getdir,
                        spec='isdir', absolute=True)
            if o == '-x': # xbrowser
                self.xb = True

    def urlGo(self):
        if self.getdir:
            from cheutils import getbin
            goOnline()
            systemcall.systemCall(
                [getbin.getBin('wget'), '-P', self.getdir] + self.items)
        else:
            from cheutils.selbrowser import Browser, BrowserError
            b = Browser(items=self.items, tb=self.tb, xb=self.xb)
            try:
                b.urlVisit()
            except BrowserError, e:
                raise UrlbatcherError(e)
                    
    def urlSearch(self):
        try:
            Urlcollector.urlCollect(self)
        except UrlcollectorError, e:
            raise UrlbatcherError(e)
        if not self.files:
            LastExit.termInit(self)
        if self.items:
            yorn = '%s\nRetrieve the above %s? yes, [No] ' \
                    % ('\n'.join(self.items),
                       spl.sPl(len(self.items),
                           ('url', 'message-id')[self.proto=='mid']))
            if raw_input(yorn).lower() in ('y', 'yes'):
                if self.proto != 'mid':
                    self.urlGo()
                else:
                    try:
                        Kiosk.kioskStore(self)
                    except KioskError, e:
                        raise UrlbatcherError(e)
        else:
            msg = 'No %s found. [Ok] ' \
                    % ('urls', 'message-ids')[self.proto=='mid']
            raw_input(msg)
        if not self.files:
            LastExit.reInit(self)


def run():
    try:
        ub = Urlbatcher()
        ub.argParser()
        ub.urlSearch()
    except UrlbatcherError, e:
        userHelp(e)
    except KeyboardInterrupt:
        print
