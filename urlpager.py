urlpager_cset = '$Hg: urlpager.py,v$'

###
# Caveat:
# If input is read from stdin, it should be of one type
# (text/plain, text/html, email) because the type detecting
# mechanism is only triggered once.
# However you should be able to run this on all kind of files,
# input is checked anew for each file.
###

import os, readline
from Urlcollector import Urlcollector, UrlcollectorError
from kiosk import Kiosk, KioskError
from tpager.Tpager import Tpager, TpagerError
from Urlregex import mailCheck, ftpCheck
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
    from cheutils.usage import Usage
    u = Usage(help=urlpager_help, rcsid=urlpager_cset)
    u.printHelp(err=error)

def goOnline():
    try:
        from cheutils import conny
        conny.appleConnect()
    except ImportError:
        pass

class UrlpagerError(Exception):
    '''Exception class for the urlpager module.'''

class Urlpager(Urlcollector, Kiosk, Tpager):
    def __init__(self):
        Kiosk.__init__(self)        # <- browse, google, kiosk, mhiers, mspool, local, xb, tb
        Urlcollector.__init__(self) # (Urlregex) <- proto, items, files, pat
        Tpager.__init__(self, name='url') # <- items, name
        self.ftp = 'ftp'            # ftp client
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
        if self.proto not in ('all', 'mid'):
            self.name = '%s %s' % (self.proto, self.name)
        elif self.proto == 'mid':
            self.name = 'message-id'
        self.name = 'unique %s' % self.name
        try:
            # as there is no ckey, interAct() returns always 0
            Tpager.interAct(self)
        except TpagerError, e:
            raise UrlpagerError(e)

    def urlGo(self):
        url, cs, conny = self.items[0], [], True
        if (self.proto == 'mailto'
                or self.proto == 'all' and mailCheck(url)):
            cs = [getbin.getBin(mailers)]
            conny = False
        elif self.getdir:
            cs = [getbin.getBin('wget'), '-P', self.getdir]
        elif self.proto == 'ftp' or ftpCheck(url):
            if not os.path.splitext(url)[1] and not url.endswith('/'):
                self.items = [url + '/']
            cs = [self.ftp]
        if not cs:
            from cheutils.selbrowser import Browser, BrowserError
            b = Browser(items=self.items, tb=self.tb, xb=self.xb)
            try:
                b.urlVisit()
            except BrowserError, e:
                raise UrlpagerError(e)
        else:
            if conny:
                goOnline()
            cs = cs + self.items
            if not self.getdir and not self.files: # program needs terminal
                tty = os.ctermid()
                cs = cs + ['<', tty, '>', tty]
                cs = ' '.join(cs)
                systemcall.systemCall(cs, sh=True)
            else:
                systemcall.systemCall(cs)

    def urlSearch(self):
        try:
            Urlcollector.urlCollect(self)
        except UrlcollectorError, e:
            raise UrlpagerError(e)
        self.urlPager()
        if not self.items:
            return
        if self.proto != 'mid':
            if self.files:
                readline.add_history(self.items[0])
                url = raw_input('\n\npress <UP> or <C-P> to edit url, '
                        '<C-C> to cancel or <RET> to accept\n%s\n'
                        % self.items[0])
            else:
                Tpager.termInit(self)
                url = raw_input('\n\npress <RET> to accept or <C-C> to cancel, '
                        'or enter url manually\n%s\n' % self.items[0])
                Tpager.reInit(self)
            if url:
                self.items = [url]
            self.urlGo()
        else:
            try:
                Kiosk.kioskStore(self)
            except KioskError, e:
                raise UrlpagerError(e)


def run():
    try:
        up = Urlpager()
        up.argParser()
        up.urlSearch()
    except UrlpagerError, e:
        userHelp(e)
