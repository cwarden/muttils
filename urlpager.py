urlpager_cset = '$Hg: urlpager.py,v$'

###
# Caveat:
# If input is read from stdin, it should be of one type
# (text/plain, text/html, email) because the type detecting
# mechanism is only triggered once.
# However you should be able to run this on all kind of files,
# input is checked anew for each file.
###

import os, readline, Urlregex
from tpager.LastExit import LastExit
from tpager.Tpager import Tpager
from Urlcollector import Urlcollector
from kiosk import Kiosk
from cheutils import getbin, systemcall

optstring = 'bd:D:f:hiIlM:np:k:r:tw:x'
mailers = ('mutt', 'pine', 'elm', 'mail') 

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

def userHelp(error=''):
    from cheutils.exnam import Usage
    u = Usage(help=urlpager_help, rcsid=urlpager_cset)
    u.printHelp(err=error)

def goOnline():
    try:
        from cheutils import conny
        conny.appleConnect()
    except ImportError:
        pass

class UrlpagerError(Exception):
    '''Exception class for this module.'''

class Urlpager(Urlcollector, Kiosk, Tpager, LastExit):
    def __init__(self):
        Kiosk.__init__(self)        # <- browse, google, kiosk, mhiers, mspool, local, xb, tb
        LastExit.__init__(self)
        Tpager.__init__(self, name='url') # <- items, name
        Urlcollector.__init__(self) # (Urlregex) <- proto, items, files, pat
        self.ftp = 'ftp'            # ftp client
        self.url = ''               # selected url
        self.getdir = ''            # download in dir via wget

    def argParser(self):
        import getopt, sys
        try:
            opts, self.files = getopt.getopt(sys.argv[1:], optstring)
        except getopt.GetoptError, e:
            raise UrlpagerError(e)
        for o, a in opts:
            if o == '-b': # don't look up msgs locally
                self.proto = 'mid'
                self.browse = True
            if o == '-d': # specific mail hierarchies
                self.proto = 'mid'
                self.mhiers = a.split(':')
            if o == '-D': # specific mail hierarchies, exclude mspool
                self.proto = 'mid'
                self.mspool = False
                self.mhiers = a.split(':')
            if o == '-f': # ftp client
                self.ftp = getbin.getBin(a)
            if o == '-h':
                userHelp()
            if o == '-I': # look for declared message-ids
                self.proto = 'mid'
                self.decl = True
            if o == '-i': # look for ids, in text w/o prot (email false positives)
                self.proto = 'mid'
            if o == '-k': # mailbox to store retrieved message
                self.proto = 'mid'
                self.kiosk = a
            if o == '-l': # only local search for message-ids
                self.proto = 'mid'
                self.local = True
            if o == '-M': # file mask
                self.proto = 'mid'
                self.mask = a
            if o == '-n': # don't search mailboxes for message-ids
                self.proto = 'mid'
                self.mhiers = None
            if o == '-p': # protocol(s)
                self.proto = a
            if o == '-r': # regex pattern to match urls against
                self.pat = a
            if o == '-x': # xbrowser
                self.xb = True
            if o == '-t': # text browser command
                self.tb = True
            if o == '-w': # download dir for wget
                from cheutils import filecheck
                self.proto = 'web'
                getdir = a
                self.getdir = filecheck.fileCheck(getdir,
                        spec='isdir', absolute=True)

    def urlPager(self):
        if not self.proto in ('all', 'mid'):
            self.name = '%s %s' % (self.proto, self.name)
        elif self.proto == 'mid':
            self.name = 'message-id'
        self.name = 'unique %s' % self.name
        self.url = Tpager.interAct(self)

    def urlGo(self):
        cs, conny = [], True
        if self.proto == 'mailto' \
                or (self.proto == 'all' and Urlregex.mailCheck(self.url)):
            cs = [getbin.getBin(mailers)]
            conny = False
        elif self.getdir:
            cs = [getbin.getBin('wget'), '-P', self.getdir]
        elif self.proto == 'ftp' or Urlregex.ftpCheck(self.url):
            if not os.path.splitext(self.url)[1] \
                    and not self.url.endswith('/'):
                self.url = self.url + '/'
            cs = [self.ftp]
        if not cs:
            from cheutils.selbrowser import Browser
            b = Browser(items=[self.url], tb=self.tb, xb=self.xb)
            b.urlVisit()
        else:
            if conny:
                goOnline()
            if not self.getdir and not self.files: # program needs terminal
                tty = os.ctermid()
                cs = cs + [self.url, '<', tty, '>', tty]
                cs = ' '.join(cs)
                systemcall.systemCall(cs, sh=True)
            else:
                cs.append(self.url)
                systemcall.systemCall(cs)

    def urlSearch(self):
        Urlcollector.urlCollect(self)
        if not self.files:
            LastExit.termInit(self)
        self.urlPager()
        if self.url:
            if self.proto != 'mid':
                self.urlGo()
            else:
                self.items = [self.url]
                Kiosk.kioskStore(self)
        if not self.files:
            try:
                LastExit.reInit(self)
            except IndexError:
                pass
