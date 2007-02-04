# $Id$'

import muttils.util
from muttils.html2text import HTML2Text
from muttils.pybrowser import Browser, BrowserError
from email.Generator import Generator
from email.Parser import Parser
from email.Errors import MessageParseError, HeaderParseError
import email, mailbox, os, re, tempfile, time, urllib, urllib2, sys

gmsgterminator = 'Create a group[8] - Google Groups[9]'
ggroups = 'http://groups.google.com/groups'
useragent = ('User-Agent', 'w3m')
urlfailmsg = 'reason of url retrieval failure: '
urlerrmsg = 'url retrieval error code: '
changedsrcview = 'source view format changed at Google'
muttone = ["-e", "'set pager_index_lines=0'",
          "-e", "'set quit=yes'", "-e", "'bind pager q quit'",
          "-e", "'push <return>'", "-f"]
mutti = ["-e", "'set uncollapse_jump'",
        "-e" "'push <search>~i\ \'%s\'<return>'", "-f"]

def mailSpool():
    '''Tries to return a sensible default for user's mail spool.
    Returns None otherwise.'''
    mailspool = os.getenv('MAIL')
    if not mailspool:
        ms = os.path.join('var', 'mail', os.environ['USER'])
        if os.path.isfile(ms):
            return ms
    elif mailspool.endswith(os.sep):
        return mailspool[:-1] # ~/Maildir/-INBOX[/]
    return mailspool

def mailHier():
    '''Returns either ~/Maildir or ~/Mail
    as first item of a list if they are directories,
    an empty list otherwise.'''
    castle = os.environ['HOME']
    for md in ('Maildir', 'Mail'):
        d = os.path.join(castle, md)
        if os.path.isdir(d):
            return [d]
    return []

def msgFactory(fp):
    try:
        p = Parser()
        return p.parse(fp, headersonly=True)
    except HeaderParseError:
        return ''

def mkUnixfrom(msg):
    '''Tries to create an improved unixfrom.'''
    if msg['return-path']:
        ufrom = msg['return-path'][1:-1]
    else:
        ufrom = email.Utils.parseaddr(msg.get('from', 'nobody'))[1]
    msg.set_unixfrom('From %s  %s' % (ufrom, time.asctime()))
    return msg


class KioskError(Exception):
    '''Exception class for the kiosk module.'''

class Kiosk(HTML2Text):
    '''
    Provides methods to search for and retrieve
    messages via their Message-ID.
    '''
    defaults = {
            'kiosk': '',
            'browse': False,
            'local': False,
            'mhiers': [],
            'mspool': False,
            'mask': None,
            'mailer': 'mail',
            'xb': '',
            'tb': '',
            }

    def __init__(self, items=None, opts={}):
        HTML2Text.__init__(self, strict=False)
        self.items = items or []

        for k in self.defaults.keys():
            setattr(self, k, opts.get(k, self.defaults[k]))

        self.msgs = []           # list of retrieved message objects
        self.muttone = True      # configure mutt for display of 1 msg only
        self.mdmask = '^(cur|new|tmp)$'

    def kioskTest(self):
        '''Provides the path to an mbox file to store retrieved messages.'''
        if not self.kiosk:
            self.kiosk = tempfile.mkstemp('.kiosk')[1]
            return
        self.kiosk = muttils.util.absolutepath(self.kiosk)
        if not os.path.exists(self.kiosk) or not os.path.getsize(self.kiosk):
            # non existant or empty is fine
            return
        if not os.path.isfile(self.kiosk):
            raise KioskError('%s: not a regular file' % self.kiosk)
        e = '%s: not a unix mailbox' % self.kiosk
        fp = open(self.kiosk, 'rb')
        try:
            testline = fp.readline()
        finally:
            fp.close()
        try:
            p = Parser()
            check = p.parsestr(testline, headersonly=True)
        except HeaderParseError, e:
            raise KioskError(e)
        if check.get_unixfrom():
            self.muttone = False
        else:
            raise KioskError('%s: not a unix mailbox' % self.kiosk)

    def hierTest(self):
        '''Checks whether given directories exist and
        creates mhiers set (unique elems) with absolute paths.'''
        if not self.mhiers:
            self.mhiers = mailHier()
        mhiers = set(self.mhiers)
        self.mhiers = set([])
        for hier in mhiers:
            abshier = muttils.util.absolutepath(hier)
            if os.path.isdir(abshier):
                self.mhiers.add(abshier)
            else:
                sys.stdout.write('%s: not a directory, skipping\n' % hier)

    def makeQuery(self, mid):
        '''Reformats Message-ID to google query.'''
        query = ({'selm': mid, 'dmode': 'source'},
                {'selm': mid})[self.browse]
        return '%s?%s' % (ggroups,  urllib.urlencode(query))

    def gooBrowse(self):
        '''Visits given urls with browser and exits.'''
        b = Browser(items=[self.makeQuery(mid) for mid in self.items],
                tb=self.tb, xb=self.xb)
        try:
            b.urlVisit()
        except BrowserError, e:
            raise KioskError(e)
        sys.exit()

    def gooRetrieve(self, mid, found, opener, header_re):
        try:
            fp = opener.open(self.makeQuery(mid))
            self.htpWrite(html=fp.read(), append=False)
            fp.close()
            liniter = iter(self.htpReadlines(nl=False))
        except urllib2.URLError, e:
            if hasattr(e, 'reason'):
                raise KioskError(urlfailmsg + e)
            if hasattr(e, 'code'):
                raise KioskError(urlerrmsg + e)
        line = ''
        try:
            while not header_re.match(line):
                line = liniter.next()
        except StopIteration:
            sys.stdout.write('%s: not at Google\n' % mid)
            time.sleep(5)
        else:
            lines = [line]
            try:
                while not line.startswith(gmsgterminator):
                    line = liniter.next()
                    lines.append(line)
            except StopIteration:
                sys.stderr.write('\n'.join(lines) + '\n')
                raise KioskError(changedsrcview)
            msg = '\n'.join(lines[:-1])
            msg = email.message_from_string(msg)
            found.append(mid)
            self.msgs.append(msg)

    def goGoogle(self):
        '''Gets messages from Google Groups.'''
        sys.stdout.write('Going google ...\n')
        if self.browse:
            self.gooBrowse()
        sys.stdout.write('*Unfortunately Google masks all email addresses*\n')
        opener = urllib2.build_opener()
        opener.addheaders = [useragent]
        header_re = re.compile(r'[A-Z][-a-zA-Z]+: ')
        muttils.util.goonline()
        found = []
        self.open()
        try:
            for mid in self.items:
                self.gooRetrieve(mid, found, opener, header_re)
        finally:
            self.close()
        self.items = [mid for mid in self.items if mid not in found]

    def leafSearch(self):
        try:
            from slrnpy.Leafnode import Leafnode
        except ImportError:
            return
        leafnode = Leafnode()
        sys.stdout.write('Searching local newsserver ...\n')
        articles, self.items = leafnode.idPath(idlist=self.items, verbose=True)
        for article in articles:
            fp = open(article, 'rb')
            try:
                msg = email.message_from_file(fp)
            except MessageParseError, e:
                raise KioskError(e)
            fp.close()
            self.msgs.append(msg)
        if self.items:
            sys.stdout.write('%s not on local server\n'
                    % muttils.util.plural(len(self.items), 'message'))

    def boxParser(self, path, maildir=False, isspool=False):
        if (not isspool and path == self.mspool
                or self.mask and self.mask.search(path) is not None):
            return
        if maildir:
            try:
                dl = os.listdir(path)
            except OSError:
                return
            for d in 'cur', 'new', 'tmp':
                if d not in dl:
                    return
            mbox = mailbox.Maildir(path, msgFactory)
        else:
            try:
                fp = open(path, 'rb')
            except IOError, e:
                sys.stdout.write('%s\n' % e)
                return
            mbox = mailbox.PortableUnixMailbox(fp, msgFactory)
        sys.stdout.write('searching %s ' % path)
        while True:
            try:
                msg = mbox.next()
                sys.stdout.write('.')
                sys.stdout.flush()
            except IOError, e:
                sys.stdout.write('\n%s\n' % e)
                break
            if msg is None:
                sys.stdout.write('\n')
                break
            msgid = msg.get('message-id','')[1:-1]
            if msgid in self.items:
                self.msgs.append(msg)
                self.items.remove(msgid)
                sys.stdout.write('\nretrieving Message-ID <%s>\n' % msgid)
                if not self.items:
                    break
        if not maildir:
            fp.close()

    def walkMhier(self, mdir):
        '''Visits mail hierarchies and parses their mailboxes.
        Detects mbox and Maildir mailboxes.'''
        for root, dirs, files in os.walk(mdir):    
            if not self.items:
                break
            rmdl = [d for d in dirs if self.mdmask.search(d) is not None]
            for d in rmdl:
                dirs.remove(d)
            for name in dirs:
                if self.items:
                    path = os.path.join(root, name)
                    self.boxParser(path, True)
            for name in files:
                if self.items:
                    path = os.path.join(root, name)
                    self.boxParser(path)

    def mailSearch(self):
        '''Announces search of mailboxes, searches spool,
        and passes mail hierarchies to walkMhier.'''
        sys.stdout.write('Searching local mailboxes ...\n')
        if self.mspool:
            self.mspool = mailSpool()
            self.boxParser(self.mspool,
                    os.path.isdir(self.mspool), isspool=True)
        self.mdmask = re.compile(r'%s' % self.mdmask)
        for mhier in self.mhiers:
            self.walkMhier(mhier)

    def masKompile(self):
        try:
            self.mask = re.compile(r'%s' % self.mask)
        except re.error, e:
            raise KioskError("%s in pattern `%s'" % (e, self.mask))

    def openKiosk(self, firstid):
        '''Opens mutt on kiosk mailbox.'''
        fp = open(self.kiosk, 'ab')
        try:
            g = Generator(fp, maxheaderlen=0)
            for msg in self.msgs:
                # delete read status and local server info
                for h in ('Status', 'Xref'):
                    del msg[h]
                if not msg.get_unixfrom():
                    msg = mkUnixfrom(msg)
                g.flatten(msg, unixfrom=True)
        finally:
            fp.close()
        self.kiosk = "'%s'" % self.kiosk
        cs = [str(self.mailer)]
        if  self.mailer[:4] != 'mutt':
            cs = [self.mailer, '-f', self.kiosk]
        elif len(self.msgs) == 1 and self.muttone:
            cs += muttone + [self.kiosk]
        else:
            mutti[-2] = mutti[-2] % firstid
            cs += mutti + [self.kiosk] 
        if not os.isatty(0):
            tty = os.ctermid()
            cs += ['<', tty, '>', tty]
        os.system(' '.join(cs))

    def kioskStore(self):
        '''Collects messages identified by ID either
        by retrieving them locally or from GoogleGroups.'''
        if self.browse:
            self.goGoogle()
        self.kioskTest()
        if self.mask:
            self.masKompile()
        itemscopy = self.items[:]
        self.leafSearch()
        if self.items and self.mhiers is not None:
            self.hierTest()
            self.mailSearch()
            if self.items:
                sys.stdout.write('%s not in specified local mailboxes\n'
                        % muttils.util.plural(len(self.items), 'message'))
        if self.items and not self.local:
            self.goGoogle()
        elif self.items:
            time.sleep(3)
        if self.msgs:
            firstid = None
            for mid in itemscopy:
                if mid not in self.items:
                    firstid = mid
                    break
            self.openKiosk(firstid)
