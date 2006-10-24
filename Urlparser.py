# $Hg: Urlparser.py,v$

import email, email.Utils, re
from email.Errors import MessageParseError

protos = ('all', 'web',
        'http', 'ftp', 'gopher',
        'mailto',
        'mid')
# finger, telnet, whois, wais?

# header tuples (to be extended)
searchkeys = ('subject', 'organization',
              'user-agent', 'x-mailer', 'x-newsreader',
              'list-id', 'list-subscribe', 'list-unsubscribe',
              'list-help', 'list-archive', 'list-url',
              'mailing-list', 'x-habeas-swe-9')

refkeys = ('references', 'in-reply-to', 'message-id', 'original-message-id')

addrkeys = ('from', 'to', 'reply-to', 'cc',
            'sender', 'x-sender', 'mail-followup-to',
            'x-apparently-to',
            'errors-to', 'x-complaints-to', 'x-beenthere')

quote_re = re.compile(r'^(> ?)+', re.MULTILINE)

def msgFactory(fp):
    try:
        return email.message_from_file(fp)
    except MessageParseError:
        return ''

def unQuote(s):
    return quote_re.sub('', s)


class UrlparserError(Exception):
    '''Exception class for this module.'''

class Urlparser(object):
    '''
    Subclass of Urlregex.
    Extracts urls from html text
    messages or mailboxes.
    '''
    def __init__(self, proto='all'):
        self.proto = proto
        self.url_re = None
        self.items = []
        self.msg = ''

    def protoTest(self):
        if self.proto not in protos:
            raise UrlparserError("`%s': invalid spec, use one of %s"
                    % (self.proto, ', '.join(protos)))

    def headParser(self, hkeys):
        for hkey in hkeys:
            vals = self.msg.get_all(hkey)
            if vals:
                pairs = email.Utils.getaddresses(vals)
                urls = [pair[1] for pair in pairs if pair[1]]
                self.items += urls

    def headSearcher(self):
        for skey in searchkeys:
            vals = self.msg.get_all(skey, [])
            for val in vals:
                urls = [u[0] for u in self.url_re.findall(val)]
                self.items += urls

    def mailDeconstructor(self, s):
        '''Checks if given string is message or mailbox.
        If no, returns string.
        Parses message/mailbox for relevant headers
        adding urls to list of items and returns
        text parts for further searching.'''
        try:
            self.msg = email.message_from_string(s)
        except MessageParseError:
            return s
        if not self.msg or not self.msg['Message-ID']:
            return s
        # else it's a message or a mailbox
        if not self.msg.get_unixfrom():
            sl = self.msgDeconstructor()
        else: # treat s like a mailbox because it might be one
            from cStringIO import StringIO
            from mailbox import PortableUnixMailbox
            sl = [] # list of strings to search
            fp = StringIO()
            fp.write(s)
            mbox = PortableUnixMailbox(fp, msgFactory)
            while self.msg is not None:
                self.msg = mbox.next()
                if self.msg:
                    sl = self.msgDeconstructor(sl)
            fp.close()
        s = '\n'.join(sl)
        return unQuote(s) # get quoted urls spanning more than 1 line

    def msgDeconstructor(self, sl=None):
        if sl is None:
            sl = []
        if self.proto != 'mid':
            if self.proto in ('all', 'mailto'):
                self.headParser(addrkeys)
            self.headSearcher()
        else:
            self.headParser(refkeys)
        for part in self.msg.walk(): # use email.Iterator?
            if part.get_content_maintype() == 'text':
                text = part.get_payload(decode=True)
                sl.append(text)
        return sl
