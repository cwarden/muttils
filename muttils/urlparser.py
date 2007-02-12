# $Id$

import cStringIO, re
import email, email.iterators, email.Utils, email.Errors
import mailbox

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

quote_re = re.compile(r'^([>|]\s*)+', re.MULTILINE)

def msgFactory(fp):
    try:
        return email.message_from_file(fp)
    except email.Errors.MessageParseError:
        return ''

def unQuote(s):
    return quote_re.sub('', s)


class UrlparserError(Exception):
    '''Exception class for the Urlparser module.'''

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

    def protoTest(self):
        if self.proto not in protos:
            raise UrlparserError("`%s': invalid spec, use one of %s"
                    % (self.proto, ', '.join(protos)))

    def headParser(self, msg, hkeys):
        for hkey in hkeys:
            vals = msg.get_all(hkey)
            if vals:
                pairs = email.Utils.getaddresses(vals)
                urls = [pair[1] for pair in pairs if pair[1]]
                self.items += urls

    def headSearcher(self, msg):
        for skey in searchkeys:
            vals = msg.get_all(skey, [])
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
            msg = email.message_from_string(s)
        except email.Errors.MessageParseError:
            return s
        if not msg or not msg['Message-ID']:
            return s
        # else it's a message or a mailbox
        if not msg.get_unixfrom():
            sl = self.msgDeconstructor(msg)
        else: # treat s like a mailbox because it might be one
            sl = [] # list of strings to search
            fp = cStringIO.StringIO()
            fp.write(s)
            mbox = mailbox.PortableUnixMailbox(fp, msgFactory)
            while msg is not None:
                msg = mbox.next()
                if msg:
                    sl = self.msgDeconstructor(msg, strings=sl)
            fp.close()
        s = '\n'.join(sl)
        return unQuote(s) # get quoted urls spanning more than 1 line

    def msgDeconstructor(self, msg, strings=None):
        sl = strings or []
        if self.proto != 'mid':
            if self.proto in ('all', 'mailto'):
                self.headParser(msg, addrkeys)
            self.headSearcher(msg)
        else:
            self.headParser(refkeys)
        for part in email.iterators.typed_subpart_iterator(msg):
            sl.append(part.get_payload())
        return sl
