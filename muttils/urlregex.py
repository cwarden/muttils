# $Id$

import util
import re

valid_protos = ['all', 'web',
        'http', 'ftp', 'gopher',
        'mailto', 'mid']
# finger, telnet, whois, wais?

serverchars = r'-.a-z0-9'
# regexes on demand
mail_re = ftp_re = None

def topdompat():
    '''Returns pattern matching top level domains, preceded by dot.'''
    generics = [
            'aero', 'arpa', 'biz', 'cat', 'com', 'coop',
            'edu', 'gov', 'info', 'int', 'jobs', 'mil', 'mobi', 'museum',
            'name', 'net', 'org', 'pro', 'root', 'travel'
            ]
    # top level domains
    tops = generics + [
            'a[cdefgilmnoqrstuwz]', 'b[abdefghijmnorstvwyz]',
            'c[acdfghiklmnoruvxyz]', 'd[ejkmoz]', 'e[ceghrstu]',
            'f[ijkmor]', 'g[abdefghilmnpqrstuwy]',
            'h[kmnrtu]', 'i[delnmoqrst]', 'j[emop]',
            'k[eghimnprwyz]', 'l[abcikrstuvy]',
            'm[acdeghklmnopqrstuvwxyz]', 'n[acefgilopruz]', 'om',
            'p[aefghklmnrstwy]', 'qa', 'r[eosuw]',
            's[abcdeghijklmnortuvyz]',
            't[cdfghjkmnoprtvwz]', 'u[agkmsyz]',
            'v[acegivu]', 'w[fs]', 'y[etu]', 'z[amw]'
            ]
    return r'\.(%s)' % '|'.join(tops)

def weburlpats(proto='', serv=serverchars, top=topdompat()):
    '''Creates 2 url patterns. The first according to protocol,
    The second may contain spaces but is enclosed in '<>'.'''
    valid = serv + r'/#~:,;?+=&%!()@'   # valid url-chars+comma+semicolon+parenthesises+@
                                        # @: filtered with webcheck, false positives with
                                        # che@*blacktrash.org* otherwise
                                        # Message-ID: <10rb6mngqccs018@corp.supernews.com>
                                        # Message-id: <20050702131039.GA10840@oreka.com>
    last = r'/a-z0-9'                   # allowed at end
    punct = r'-.,;:?!)('                # punctuation
    dom = r'''
        \b                  # start at word boundary
        %(proto)s           # protocol or empty
        [%(serv)s] +        # followed by 1 or more server char
        %(top)s             # top level preceded by dot
        (                   # 0 or 1 group
          (/|:\d+)          #  group slash or port
          (                 #  0 or more group
            [%(valid)s] +   #   1 or more valid  
            [%(last)s]      #   1 ending char
          ) *
        ) ?
        (?=                 # look-ahead non-consumptive assertion
          [%(punct)s] *     #  0 or more punctuation
          [^%(valid)s]      #  non-url char
        |                   # or else
          $                 #  then end of the string
        )
        ''' % vars()
    spdom = r'''
        (?<=<)               # look behind for '<'
        %(proto)s            # protocol or empty
        [%(serv)s\s] +       # server or space (space to be removed)
        %(top)s              # top level dom preceded by dot
        (                    # 0 or 1 group
          (/|:\d+) \s*       #  slash or port + 0 or more spaces
          [%(valid)s\s] *    #  valid or space (space to be removed)
        ) ?
        (?=>)                # lookahead for '>'
        ''' % vars()
    return dom, spdom

def mailpat(serv=serverchars, top=topdompat()):
    '''Creates pattern for email addresses,
    grabbing those containing a subject first.'''
    address = '[%(serv)s]+@[%(serv)s]+%(top)s' % vars()
    return r'''
        \b(                 # word boundary and group open
          mailto:           #  mandatory mailto
          %(address)s       #  address
          \?subject=        #  ?subject=
          [^>]              #  any except >
        |
          (mailto:)?        #  optional mailto
          %(address)s       #  address
        )\b                 # close group and word boundary
        ''' % { 'address': address }

def nntppat():
    '''Creates pattern for either nntp protocol or
    attributions with message-ids.'''
    return r'''
        (                                              # 1 group
          msgid|news|nntp|message(-id)?|article|MID    #  attrib strings
        )
        (                                              # 1 group
          :\s*|\s+                                     # colon+optspace or space+
        )
        <{,2}                                          # 0--2 '<'
        '''

def midpat(serv=serverchars, top=topdompat()):
    '''Creates pattern for message ids.'''
    idy = serv + r'#~?+=&%!$\]['   # valid message-id-chars ### w/o ':/'?
    return r'''
        [%(idy)s] +     # one or more valid id char
        @
        [%(serv)s] +    # one or more server char
        %(top)s         # top level domain
        ''' % vars()

def declmidpat():
    '''Returns pattern for message id, prefixed with "attribution".'''
    return r'(\b%s%s\b)' % (nntppat(), midpat())

def wipepat():
    '''Creates pattern for useless headers in message _bodies_ (OLE!).'''
    headers = (
            'received', 'references', 'message-id', 'in-reply-to',
            'delivered-to', 'list-id', 'path', 'return-path',
            'newsgroups', 'nntp-posting-host',
            'xref', 'x-id', 'x-abuse-info', 'x-trace', 'x-mime-autoconverted'
            )
    headers = r'(%s)' % '|'.join(headers)
    header = r'''
        (\n|^)          # newline or very start
        %s:             # header followed by colon &
        .+              # greedy anything (but newline)
        (               # 0 or more group
          \n            #  newline followed by
          [ \t]+        #  greedy spacetabs
          .+            #  greedy anything
        ) *?
        ''' % headers
    return r'%s|%s' % (header, declmidpat())

def get_mailre():
    '''Returns email address pattern on demand.'''
    global mail_re
    mail_re = (mail_re or
            re.compile(r'(%s)' % mailpat(), re.IGNORECASE|re.VERBOSE))
    return mail_re

def get_ftpre():
    global ftp_re
    ftp_re = ftp_re or re.compile(r'(s?ftp://|ftp\.)', re.IGNORECASE)
    return ftp_re
    
# filter functions
# also usable by "outside" scripts, eg. urlpager

def webcheck(url):
    '''Returns True if url is not email address.'''
    return not get_mailre().match(url)

def ftpcheck(url):
    '''Returns True if url is ftp location.'''
    return get_ftpre().match(url)

def httpcheck(url):
    '''Returns True if url is neither mail address nor ftp location.'''
    return not get_mailre().match(url) and not get_ftpre().match(url)

def mailcheck(url):
    '''Returns True if url is email address.'''
    return get_mailre().match(url)

filterdict = { 'web':    webcheck,
               'ftp':    ftpcheck,
               'http':   httpcheck,
               'mailto': mailcheck }


class urlregex(object):
    '''
    Provides functions to extract urls from text,
    customized by attributes.
    Detects also www-urls that don't start with a protocol and
    urls spanning more than 1 line if they are enclosed in '<>'.
    '''
    def __init__(self, proto='all', decl=False, uniq=True):
        self.proto = proto
        self.decl = decl         # list only declared urls
        self.uniq = uniq         # list only unique urls
        self.url_re = None       # that's what it's all about
        self.kill_re = None      # customized pattern to find non url chars
        self.protocol = ''       # pragmatic proto (may include www., ftp.)
        self.proto_re = None
        self.cpan = ''
        self.ctan = ''
        self.items = []

    def setprotocol(self):
        mailto = 'mailto:\s?' # needed for proto=='all'
        http = r'(https?://|www\.)'
        ftp = r'(s?ftp://|ftp\.)'
        gopher = r'gopher://'
        # finger, telnet, whois, wais?
        if self.proto in ('all', 'web'):
            protocols = [mailto, http, ftp, gopher][self.proto=='web':]
            protocol = r'(%s)' % '|'.join(protocols)
        else:                  ## singles
            self.decl = True
            protocol = eval(self.proto)
        self.protocol = r'(url:\s?)?%s' % protocol

    def getraw(self):
        '''Returns raw patterns according to protocol.'''
        self.setprotocol()
        url, spurl = weburlpats(self.protocol)
        if self.decl:
            return r'(%s|%s)' % (spurl, url)
        any_url, any_spurl = weburlpats()
        return (r'(%s|%s|%s|%s|%s)' %
                    (mailpat(), spurl, any_spurl, url, any_url))

    def unideluxe(self):
        '''remove duplicates deluxe:
        of http://www.blacktrash.org, www.blacktrash.org
        keep only the first, declared version.'''
        truncs = [self.proto_re.sub('', u) for u in self.items]
        deluxurls = []
        for i in xrange(len(self.items)):
            url = self.items[i]
            trunc = truncs[i]
            if truncs.count(trunc) == 1 or len(url) > len(trunc):
                deluxurls.append(url)
        self.items = deluxurls

    def urlfilter(self):
        if not self.decl and self.proto in filterdict:
            self.items = filter(filterdict[self.proto], self.items)
        if self.uniq:
            self.items = list(set(self.items))
            if self.proto != 'mid' and not self.decl:
                self.unideluxe()

    def urlobject(self, search=True):
        '''Creates customized regex objects of url.'''
        if self.proto not in valid_protos:
            raise util.DeadMan(
                    '%s: invalid protocol parameter, use one of:\n%s'
                    % (self.proto, ', '.join(valid_protos)))
        if self.proto == 'mailto':# be pragmatic and list not only declared
            self.url_re = get_mailre()
            self.proto_re = re.compile(r'^mailto:')
        elif self.proto != 'mid':
            self.url_re = re.compile(self.getraw(), re.IGNORECASE|re.VERBOSE)
            if search:
                self.kill_re = re.compile(r'^url:\s?|\s+', re.IGNORECASE)
            if not self.decl:
                self.proto_re = re.compile(r'^%s' % self.protocol,
                        re.IGNORECASE)
        elif self.decl:
            self.url_re = re.compile(declmidpat(), re.IGNORECASE|re.VERBOSE)
            if search:
                self.kill_re = re.compile(nntppat(), re.IGNORECASE|re.VERBOSE)
        else:
            self.url_re = re.compile(r'(\b%s\b)' % midpat(),
                    re.IGNORECASE|re.VERBOSE)

    def findurls(self, text):
        '''Conducts a search for urls in text.
        Data is supposed to be text but tested whether
        it's a message/Mailbox (then passed to urlparser).'''
        self.urlobject() # compile url_re
        if self.proto != 'mid':
            wipe_re = re.compile(wipepat(), re.IGNORECASE|re.VERBOSE)
            text = wipe_re.sub('', text)
            rawcan = r'C%sAN:\s*/?([a-zA-Z]+?)'
            for can in [(self.cpan, 'P'), (self.ctan, 'T')]:
                if can[0]:
                    cansub = r'%s/\1' % can[0].rstrip('/')
                    text = re.sub(rawcan % can[1], cansub, text)
        urls = [u[0] for u in self.url_re.findall(text)]
        if self.kill_re:
            urls = [self.kill_re.sub('', u) for u in urls]
        self.items += urls
        self.urlfilter()
        self.items.sort()
