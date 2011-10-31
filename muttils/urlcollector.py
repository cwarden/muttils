# $Id$

import os, re, sys, tempfile
import email, email.Iterators, email.Utils, email.Errors
import mailbox
from muttils import urlregex, util

def _msgfactory(fp):
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
    quote_re = re.compile(r'^([>|]\s*)+', re.MULTILINE)

    def __init__(self, ui, files=None):
        urlregex.urlregex.__init__(self, ui)
        # ^ items
        self.ui = ui
        self.files = files

    def getaddr(self, msg, *headers):
        for header in headers:
            vals = msg.get_all(header)
            if vals:
                pairs = email.Utils.getaddresses(vals)
                self.items += [addr for rname, addr in pairs if addr]

    def msgharvest(self, msg):
        sl = []
        if self.ui.proto != 'mid':
            if self.ui.proto in ('all', 'mailto'):
                self.getaddr(msg, 'from', 'to', 'reply-to', 'cc', 'sender',
                             'x-sender', 'mail-followup-to', 'x-apparently-to',
                             'errors-to', 'x-beenthere')
            searchheads = ['subject', 'organization', 'user-agent', 'x-mailer',
                           'x-mailer-info', 'x-newsreader', 'list-subscribe',
                           'list-unsubscribe', 'list-help', 'list-archive',
                           'list-url', 'mailing-list', 'x-complaints-to',
                           'x-habeas-swe-9']
            for head in searchheads:
                vals = msg.get_all(head)
                if vals:
                    sl += vals
        else:
            self.getaddr(msg, 'references', 'in-reply-to', 'message-id',
                         'original-message-id')
        # revert resent messages to previous content-type
        oldct = msg['old-content-type']
        if oldct:
            del msg['content-type']
            msg['Content-Type'] = oldct
        for part in email.Iterators.typed_subpart_iterator(msg):
            # try getting quoted urls spanning more than 1 line
            s = self.quote_re.sub('', part.get_payload(decode=True))
            # handle DelSp (rfc 3675)
            ct = part.get('content-type', '').lower()
            if ct.find('delsp=yes') > -1:
                s = s.replace(' \n', '')
            sl.append(s)
        return sl

    def filedeconstructor(self, fn):
        '''Checks if given file object is message or mailbox.
        If no, returns text contents of file or empty string if file is binary.
        Parses message/mailbox for relevant headers adding urls to list of items
        and returns text parts for further searching.'''
        # binary check from mercurial.util
        fp = open(fn, 'rb')
        try:
            s = fp.read()
            if '\0' in s:
                return ''
            elif self.ui.text:
                return s
            msg = _msgfactory(fp)
            if not msg:
                return s
            # else it's a message or a mailbox
            if not msg['message-id']:
                hint = ('make sure input is a raw message,'
                        ' in mutt: unset pipe_decode')
                raise util.DeadMan('no message-id found', hint=hint)
            if not msg.get_unixfrom():
                sl = self.msgharvest(msg)
            else: # treat s like a mailbox because it might be one
                sl = [] # list of strings to search
                mbox = mailbox.PortableUnixMailbox(fp, _msgfactory)
                while msg is not None:
                    msg = mbox.next()
                    if msg:
                        sl += self.msgharvest(msg)
        finally:
            fp.close()
        return '\n'.join(sl)

    def urlcollect(self):
        '''Harvests urls from stdin or files.'''
        if not self.files: # stdin
            tempname = tempfile.mkstemp(prefix='urlcollector.')[1]
            fp = open(tempname, 'wb')
            try:
                fp.write(sys.stdin.read())
            finally:
                fp.close()
            text = self.filedeconstructor(tempname)
            os.unlink(tempname)
        else:
            textlist = []
            for f in self.files:
                textlist.append(self.filedeconstructor(util.absolutepath(f)))
            text = '\n'.join(textlist)
        if text:
            self.findurls(text)
        if self.ui.pat and self.items:
            try:
                ui_re = re.compile(r'%s' % self.ui.pat, re.IGNORECASE)
            except re.error, err:
                raise util.DeadMan("%s in pattern `%s'" % (err, self.ui.pat))
            self.items = [i for i in self.items if ui_re.search(i)]
