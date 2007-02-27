# $Id$'

import html2text, pybrowser, util
import email, email.Generator, email.Parser, email.Errors
import mailbox, os, re, tempfile, time, sys, urllib, urllib2

gmsgend = r'^[A-Z]([a-zA-Z -]+\[\d+\]){3,}'
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

def getmspool():
    '''Tries to return a sensible default for user's mail spool.'''
    mailspool = os.getenv('MAIL', '')
    if not mailspool:
        ms = os.path.join('var', 'mail', os.environ['USER'])
        if os.path.isfile(ms):
            return ms
    elif mailspool.endswith(os.sep):
        return mailspool[:-1] # ~/Maildir/-INBOX[/]
    return mailspool

def getmhier():
    '''Returns either ~/Maildir or ~/Mail
    as first item of a list if they are directories,
    an empty list otherwise.'''
    castle = os.environ['HOME']
    for md in ('Maildir', 'Mail'):
        d = os.path.join(castle, md)
        if os.path.isdir(d):
            return [d]
    return []

def msgfactory(fp):
    try:
        p = email.Parser.HeaderParser()
        return p.parse(fp, headersonly=True)
    except email.Errors.HeaderParseError:
        return ''

def mkunixfrom(msg):
    '''Tries to create an improved unixfrom.'''
    if msg['return-path']:
        ufrom = msg['return-path'][1:-1]
    else:
        ufrom = email.Utils.parseaddr(msg.get('from', 'nobody'))[1]
    msg.set_unixfrom('From %s  %s' % (ufrom, time.asctime()))
    return msg


class kiosk(html2text.html2text):
    '''
    Provides methods to search for and retrieve
    messages via their Message-ID.
    '''
    defaults = {
            'kiosk': '',
            'browse': False,
            'local': False,
            'news': False,
            'mhiers': '',
            'specdirs': '',
            'mask': None,
            'app': '',
            }

    def __init__(self, ui, items=None, opts={}):
        html2text.html2text.__init__(self, strict=False)
        self.ui = ui
        self.ui.updateconfig()
        self.items = items or []
        util.updateattribs(self, opts)
        self.mspool = ''         # path to local mail spool
        self.msgs = []           # list of retrieved message objects
        self.muttone = True      # configure mutt for display of 1 msg only
        self.mdmask = '^(cur|new|tmp)$'

    def kiosktest(self):
        '''Provides the path to an mbox file to store retrieved messages.'''
        if not self.kiosk:
            self.kiosk = tempfile.mkstemp('.kiosk')[1]
            return
        self.kiosk = util.absolutepath(self.kiosk)
        if not os.path.exists(self.kiosk) or not os.path.getsize(self.kiosk):
            # non existant or empty is fine
            return
        if not os.path.isfile(self.kiosk):
            raise util.DeadMan('%s: not a regular file' % self.kiosk)
        fp = open(self.kiosk, 'rb')
        try:
            testline = fp.readline()
        finally:
            fp.close()
        try:
            p = email.Parser.Parser()
            check = p.parsestr(testline, headersonly=True)
        except email.Errors.HeaderParseError, inst:
            raise util.DeadMan(inst)
        if check.get_unixfrom():
            self.muttone = False
        else:
            raise util.DeadMan('%s: not a unix mailbox' % self.kiosk)

    def getmhiers(self):
        '''Checks whether given directories exist and
        creates mhiers set (unique elems) with absolute paths.'''
        if self.mhiers or self.specdirs: # cmdline priority
            # specdirs have priority
            mhiers = self.specdirs or self.mhiers
            # split colon-separated list from cmdline
            mhiers = mhiers.split(':')
        else:
            mhiers = self.ui.configitem('messages', 'maildirs')
            if mhiers is not None:
                mhiers = [i.strip() for i in mhiers.split(',')]
            else:
                mhiers = getmhier()
        # create set of unique elements
        self.mhiers = set()
        for hier in mhiers:
            abshier = util.absolutepath(hier)
            if os.path.isdir(abshier):
                self.mhiers.add(abshier)
            else:
                sys.stdout.write('%s: not a directory, skipping\n' % hier)

    def makequery(self, mid):
        '''Reformats Message-ID to google query.'''
        query = ({'selm': mid, 'dmode': 'source'},
                {'selm': mid})[self.browse]
        return '%s?%s' % (ggroups,  urllib.urlencode(query))

    def goobrowse(self):
        '''Visits given urls with browser and exits.'''
        items = [self.makequery(mid) for mid in self.items]
        b = pybrowser.browser(parentui=self.ui, items=items, app=self.app)
        b.urlvisit()
        sys.exit()

    def gooretrieve(self, mid, found, opener, header_re, bottom_re):
        try:
            fp = opener.open(self.makequery(mid))
            self.htwrite(ht=fp.read(), append=False)
            fp.close()
            liniter = iter(self.htreadlines(nl=False))
        except urllib2.URLError, inst:
            if hasattr(inst, 'reason'):
                raise util.DeadMan(urlfailmsg + inst)
            if hasattr(inst, 'code'):
                raise util.DeadMan(urlerrmsg + inst)
        line = ''
        try:
            while not header_re.match(line):
                line = liniter.next()
        except StopIteration:
            sys.stdout.write('%s: not at google\n' % mid)
            time.sleep(5)
        else:
            lines = [line]
            try:
                while not bottom_re.match(line):
                    line = liniter.next()
                    lines.append(line)
            except StopIteration:
                sys.stderr.write('\n'.join(lines) + '\n')
                raise util.DeadMan(changedsrcview)
            msg = '\n'.join(lines[:-1])
            msg = email.message_from_string(msg)
            found.append(mid)
            self.msgs.append(msg)

    def gogoogle(self):
        '''Gets messages from Google Groups.'''
        sys.stdout.write(
                'note: google masks all email addresses\ngoing google ...\n')
        util.goonline()
        opener = urllib2.build_opener()
        opener.addheaders = [useragent]
        header_re = re.compile(r'[A-Z][-a-zA-Z]+: ')
        bottom_re = re.compile(gmsgend, re.MULTILINE)
        found = []
        self.open()
        try:
            for mid in self.items:
                self.gooretrieve(mid, found, opener, header_re, bottom_re)
        finally:
            self.close()
        self.items = [mid for mid in self.items if mid not in found]

    def leafsearch(self):
        '''Tries searching a local news spool.
        Works only with leafnode <= 1.5 at the moment.'''
        p = os.popen('newsq 2> %s' % os.devnull)
        r = p.readline()
        # eg.:
        # 'Contents of queue in directory /var/spool/news/out.going:\n'
        if not r:
            sys.stdout.write('no leafnode news spool detected\n')
            return
        newsout = r.split(':')[0].split()[-1]
        iddir = os.path.join(os.path.dirname(newsout), 'message.id')
        anglist = ['<%s>' % i for i in self.items]
        sys.stdout.write('Searching local newsserver ...\n')
        for root, dirs, files in os.walk(iddir):
            for fn in files:
                if fn in anglist:
                    sys.stdout.write('retrieving Message-ID %s\n' % fn)
                    try:
                        f = open(os.path.join(root, fn), 'rb')
                        try:
                            msg = email.message_from_file(f)
                        finally:
                            f.close()
                    except email.Errors.MessageParseError, inst:
                        raise util.DeadMan(inst)
                    self.msgs.append(msg)
                    self.items.remove(fn[1:-1])
        if self.items:
            sys.stdout.write('%s not on local server\n'
                    % util.plural(len(self.items), 'message'))

    def boxparser(self, path, maildir=False, isspool=False):
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
            mbox = mailbox.Maildir(path, msgfactory)
        else:
            try:
                fp = open(path, 'rb')
            except IOError, inst:
                sys.stdout.write('%s\n' % inst)
                return
            mbox = mailbox.PortableUnixMailbox(fp, msgfactory)
        sys.stdout.write('searching %s ' % path)
        while True:
            try:
                msg = mbox.next()
                sys.stdout.write('.')
                sys.stdout.flush()
            except IOError, inst:
                sys.stdout.write('\n%s\n' % inst)
                break
            if msg is None:
                sys.stdout.write('\n')
                break
            msgid = msg.get('message-id', '').strip('<>')
            if msgid in self.items:
                self.msgs.append(msg)
                self.items.remove(msgid)
                sys.stdout.write('\nretrieving Message-ID <%s>\n' % msgid)
                if not self.items:
                    break
        if not maildir:
            fp.close()

    def walkmhier(self, mdir):
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
                    self.boxparser(path, True)
            for name in files:
                if self.items:
                    path = os.path.join(root, name)
                    self.boxparser(path)

    def mailsearch(self):
        '''Announces search of mailboxes, searches spool,
        and passes mail hierarchies to walkmhier.'''
        sys.stdout.write('Searching local mailboxes ...\n')
        if not self.specdirs: # include mspool
            self.mspool = getmspool()
            if self.mspool:
                self.boxparser(self.mspool,
                        os.path.isdir(self.mspool), isspool=True)
        self.mdmask = re.compile(r'%s' % self.mdmask)
        for mhier in self.mhiers:
            self.walkmhier(mhier)

    def maskompile(self):
        try:
            self.mask = re.compile(r'%s' % self.mask)
        except re.error, inst:
            raise util.DeadMan("%s in pattern `%s'" % (inst, self.mask))

    def openkiosk(self, firstid):
        '''Opens mutt on kiosk mailbox.'''
        fp = open(self.kiosk, 'ab')
        try:
            g = email.Generator.Generator(fp, maxheaderlen=0)
            for msg in self.msgs:
                # delete read status and local server info
                for h in ('status', 'xref'):
                    del msg[h]
                if not msg.get_unixfrom():
                    msg = mkunixfrom(msg)
                g.flatten(msg, unixfrom=True)
        finally:
            fp.close()
        mailer = self.ui.configitem('messages', 'mailer')
        cs = [mailer]
        if  mailer[:4] != 'mutt':
            cs = [mailer, '-f', self.kiosk]
        elif len(self.msgs) == 1 and self.muttone:
            cs += muttone + [self.kiosk]
        else:
            mutti[-2] = mutti[-2] % firstid
            cs += mutti + [self.kiosk] 
        util.systemcall(cs)

    def kioskstore(self):
        '''Collects messages identified by ID either
        by retrieving them locally or from GoogleGroups.'''
        if self.browse:
            self.goobrowse()
        self.kiosktest()
        itemscopy = self.items[:]
        self.leafsearch()
        if self.items and not self.news:
            self.getmhiers()
            if self.mask:
                self.maskompile()
            self.mailsearch()
            if self.items:
                sys.stdout.write('%s not in specified local mailboxes\n'
                        % util.plural(len(self.items), 'message'))
        if self.items and not self.local:
            self.gogoogle()
        elif self.items:
            time.sleep(3)
        if self.msgs:
            firstid = None
            for mid in itemscopy:
                if mid not in self.items:
                    firstid = mid
                    break
            self.openkiosk(firstid)
