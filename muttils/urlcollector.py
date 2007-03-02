# $Id$

import urlregex, util
import cStringIO, re, sys
import email, email.Iterators, email.Utils, email.Errors
import mailbox

# header tuples (to be extended)
searchheads = ['subject', 'organization',
              'user-agent', 'x-mailer', 'x-newsreader',
              'list-subscribe', 'list-unsubscribe',
              'list-help', 'list-archive', 'list-url',
              'mailing-list', 'x-habeas-swe-9']

refheads = ['references', 'in-reply-to', 'message-id', 'original-message-id']

addrheads = ['from', 'to', 'reply-to', 'cc',
            'sender', 'x-sender', 'mail-followup-to',
            'x-apparently-to',
            'errors-to', 'x-complaints-to', 'x-beenthere']

quote_re = re.compile(r'^([>|]\s*)+', re.MULTILINE)

def msgfactory(fp):
    try:
        fp.seek(0)
        return email.message_from_file(fp)
    except email.Errors.MessageParseError:
        return None


class urlcollector(urlregex.urlregex):
    '''
    Provides function to retrieve urls
    from files or input stream.
    '''
    def __init__(self, ui, files=None):
        urlregex.urlregex.__init__(self, ui)
        # ^ items
        self.ui = ui
        self.files = files or [] # files to search

    def headparser(self, msg, hkeys):
        for hkey in hkeys:
            vals = msg.get_all(hkey)
            if vals:
                pairs = email.Utils.getaddresses(vals)
                urls = [pair[1] for pair in pairs if pair[1]]
                self.items += urls

    def msgharvest(self, msg, strings=None):
        sl = strings or []
        if self.ui.proto != 'mid':
            if self.ui.proto in ('all', 'mailto'):
                self.headparser(msg, addrheads)
            for skey in searchheads:
                vals = msg.get_all(skey)
                if vals:
                    sl += vals
        else:
            self.headparser(msg, refheads)
        for part in email.Iterators.typed_subpart_iterator(msg):
            sl.append(part.get_payload(decode=True))
        return sl

    def filedeconstructor(self, fp):
        '''Checks if given file object is message or mailbox.
        If no, returns text contents of file or empty string if file is binary.
        Parses message/mailbox for relevant headers adding urls to list of items
        and returns text parts for further searching.'''
        # binary check from mercurial.util
        s = fp.read(4096)
        if '\0' in s:
            return ''
        msg = msgfactory(fp)
        if not msg or not msg['Message-ID']:
            fp.seek(0)
            return fp.read()
        # else it's a message or a mailbox
        if not msg.get_unixfrom():
            sl = self.msgharvest(msg)
        else: # treat s like a mailbox because it might be one
            sl = [] # list of strings to search
            mbox = mailbox.PortableUnixMailbox(fp, msgfactory)
            while msg is not None:
                msg = mbox.next()
                if msg:
                    sl = self.msgharvest(msg, strings=sl)
        s = '\n'.join(sl)
        # try getting quoted urls spanning more than 1 line
        return quote_re.sub('', s)

    def urlcollect(self):
        '''Harvests urls from stdin or files.'''
        textlist = []
        if not self.files: # read from stdin
            fp = sys.stdin
            try: # not every stdin file object is seekable
                fp.seek(0)
            except IOError:
                fp = cStringIO.StringIO()
                fp.write(sys.stdin.read())
            text = self.filedeconstructor(fp)
            fp.close()
            textlist.append(text)
        else:
            for f in self.files:
                f = util.absolutepath(f)
                try:
                    fp = open(f, 'rb')
                except IOError, inst:
                    raise util.DeadMan(inst)
                try:
                    text = self.filedeconstructor(fp)
                    textlist.append(text)
                finally:
                    fp.close()
        text = '\n'.join(textlist)
        if text:
            self.findurls(text)
        if self.ui.pat and self.items:
            try:
                self.ui.pat = re.compile(r'%s' % self.ui.pat, re.I)
            except re.error, err:
                raise util.DeadMan("%s in pattern `%s'" % (err, self.ui.pat))
            self.items = filter(lambda i: self.ui.pat.search(i), self.items)
