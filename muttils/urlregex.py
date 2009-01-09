# $Id$

import util
import re

valid_protos = ['all', 'web', 'http', 'ftp', 'gopher', 'mailto', 'mid']
# finger, telnet, whois, wais?

# regexes on demand (web, mail, ftp)
demand_re = {}

_unreserved = r'a-z0-9\-._~'

def _hostname(generic=False):
    '''Returns hostname pattern
    for all top level domains or just generic domains.'''
    domainlabel = r'[a-z0-9]+([-a-z0-9]+[a-z0-9])?'
    # generic domains
    generics = ['aero', 'arpa', 'biz', 'cat', 'com', 'coop',
                'edu', 'gov', 'info', 'int', 'jobs', 'mil', 'mobi', 'museum',
                'name', 'net', 'org', 'pro', 'root', 'travel']
    # top level domains
    tops = generics + ['a[cdefgilmnoqrstuwz]', 'b[abdefghijmnorstvwyz]',
                       'c[acdfghiklmnoruvxyz]', 'd[ejkmoz]', 'e[ceghrstu]',
                       'f[ijkmor]', 'g[abdefghilmnpqrstuwy]',
                       'h[kmnrtu]', 'i[delnmoqrst]', 'j[emop]',
                       'k[eghimnprwyz]', 'l[abcikrstuvy]',
                       'm[acdeghklmnopqrstuvwxyz]', 'n[acefgilopruz]', 'om',
                       'p[aefghklmnrstwy]', 'qa', 'r[eosuw]',
                       's[abcdeghijklmnortuvyz]',
                       't[cdfghjkmnoprtvwz]', 'u[agkmsyz]',
                       'v[acegivu]', 'w[fs]', 'y[etu]', 'z[amw]']
    if generic:
        tds = generics
    else:
        tds = tops
    # a sequence of domainlabels + top domain
    return r'(%s\.)+(%s)' % (domainlabel, '|'.join(tds))

def _weburlpats(search, proto=''):
    '''Creates 2 url patterns. The first according to protocol,
    The second may contain spaces but is enclosed in '<>'.
    If no protocol is given the pattern matches only
    generic top level domains:
        gmx.net:    counts as url
        gmx.de:     does not as url
        www.gmx.de: counts as url
    This seems a reasonable compromise between the goal to find
    malformed urls too and false positives -- especially as we
    treat "www" as sort of inofficial scheme.'''
    gendelims = r':/?[\]@' # w/o fragment separator "#"
    subdelims = r"!$&'()*+,;="
    reserved = gendelims + subdelims
    escaped = r'%[0-9a-f]{2}' # % 2 hex
    uric = r'([%s%s]|%s)' % (_unreserved, reserved, escaped)
    if search:
        hostport = r'%s(:\d+)?' % _hostname(generic=not proto)
    else:
        hostnum = r'(\d+\.){3}\d+'
        hostport = r'(%s|%s)(:\d+)?' % (_hostname(generic=not proto), hostnum)
    dom = r'''
        \b                  # start at word boundary
        %(proto)s           # protocol or empty
        %(hostport)s        # host and optional port (no login [yet])
        (                   # 0 or 1 group
          /                 #   slash
          %(uric)s +        #   1 or more uri chars
          (                 #   0 or 1 group
            \#              #     fragment separator
            %(uric)s +      #     1 or more uri chars
          ) ?
        ) ?
        ''' % vars()
    spdom = r'''
        (?<=<)              # look behind for '<'
        %(proto)s           # protocol or empty
        %(hostport)s        # host and optional port (no login [yet])
        (                   # 0 or 1 group
          /                 #   slash
          (%(uric)s|\s) +   #   1 or more uri chars or space
          (                 #   0 or 1 group
            \#              #     fragment separator
            (%(uric)s|\s) + #     1 or more uri chars or space
          ) ?
        ) ?
        (?=>)               # lookahead for '>'
        ''' % vars()
    return dom, spdom

def _mailpat():
    '''Creates pattern for email addresses,
    grabbing those containing a subject first.'''
    address = '[%s]+@%s' % (_unreserved, _hostname())
    return r'''
        \b(                 # word boundary and group open
          mailto:           #  mandatory mailto
          %(address)s       #  address
          \?subject=        #  ?subject=
          [^>]+             #  any except >
        |
          (mailto:) ?       #  optional mailto
          %(address)s       #  address
        )\b                 # close group and word boundary
        ''' % { 'address': address }

def _nntppat():
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

def _midpat():
    '''Creates pattern for message ids.'''
    return r'[a-z0-9\-._#~?+=&%%!$[\]]{9,}@%s' % _hostname()

def _declmidpat():
    '''Returns pattern for message id, prefixed with "attribution".'''
    return r'(\b%s%s\b)' % (_nntppat(), _midpat())

def _get_mailre():
    '''Returns email address pattern on demand.'''
    try:
        mailre = demand_re['mail']
    except KeyError:
        mailre = demand_re['mail'] = re.compile(r'(%s)' % _mailpat(),
                                                re.IGNORECASE|re.VERBOSE)
    return mailre

def _webcheck(url):
    return not _get_mailre().match(url)

def webschemecomplete(url):
    '''Returns url with protocol scheme prepended if needed.
    Used by pybrowser.'''
    try:
        webre = demand_re['web']
    except KeyError:
        webre = demand_re['web'] = re.compile(r'(https?|s?ftp|gopher)://',
                                              re.IGNORECASE)
    if webre.match(url):
        return url
    for scheme in ('ftp', 'gopher'):
        if url.startswith('%s.' % scheme):
            return '%s://%s' % (scheme, url)
    return 'http://%s' % url

def ftpcheck(url):
    '''Returns True if url is ftp location.
    Used by urlpager.'''
    try:
        ftpre = demand_re['ftp']
    except KeyError:
        ftpre = demand_re['ftp'] = re.compile(r'(s?ftp://|ftp\.)',
                                              re.IGNORECASE) 
    return ftpre.match(url)

def mailcheck(url):
    '''Returns True if url is email address.
    Used by urlpager.'''
    return _get_mailre().match(url)

class urlregex(object):
    '''
    Provides functions to extract urls from text,
    customized by attributes.
    Detects also www-urls that don't start with a protocol and
    urls spanning more than 1 line if they are enclosed in '<>'.
    '''
    url_re = None
    items = []

    def __init__(self, ui, uniq=True):
        self.ui = ui             # proto, decl
        self.uniq = uniq         # list only unique urls

    def setprotocol(self):
        mailto = 'mailto:\s?' # needed for proto=='all'
        http = r'(https?://|www\.)'
        ftp = r'(s?ftp://|ftp\.)'
        gopher = r'gopher(://|\.)'
        # finger, telnet, whois, wais?
        if self.ui.proto in ('all', 'web'):
            protocols = [http, ftp, gopher]
            if self.ui.proto == 'all':
                protocols.append(mailto)
            return r'(%s)' % '|'.join(protocols)
        self.ui.decl = True
        protocol = eval(self.ui.proto)
        return r'(url:\s?)?%s' % protocol

    def getraw(self, search):
        '''Returns raw patterns according to protocol.'''
        url, spurl = _weburlpats(search, proto=self.setprotocol())
        if self.ui.decl:
            return r'(%s|%s)' % (spurl, url)
        any_url, any_spurl = _weburlpats(search)
        return (r'(%s|%s|%s|%s|%s)'
                % (_mailpat(), spurl, any_spurl, url, any_url))

    def urlfilter(self):
        '''Filters out urls not in given scheme and duplicates.'''
        filterdict = {'web': _webcheck, 'mailto': mailcheck}
        if not self.ui.decl and self.ui.proto in filterdict:
            self.items = [i for i in self.items
                          if filterdict[self.ui.proto](i)]
        if self.uniq:
            self.items = set(self.items)
            if self.ui.proto != 'mid':
                proto_re = re.compile(r'^((https?|s?ftp|gopher)://|mailto:)',
                                      re.IGNORECASE)
                truncs = [proto_re.sub('', u, 1) for u in self.items]
                pairs = zip(self.items, truncs)
                self.items = []
                for u, t in pairs:
                    if truncs.count(t) == 1 or len(u) > len(t):
                        self.items.append(u)
            else:
                self.items = list(self.items)

    def urlobject(self, search=True):
        '''Creates customized regex objects of url.'''
        kill_re = None
        if self.ui.proto not in valid_protos:
            raise util.DeadMan(self.ui.proto,
                               ': invalid protocol parameter, use one of:\n',
                               ', '.join(valid_protos))
        if self.ui.proto == 'mailto':# be pragmatic and list not only declared
            self.url_re = _get_mailre()
        elif self.ui.proto != 'mid':
            self.url_re = re.compile(self.getraw(search),
                                     re.IGNORECASE|re.VERBOSE)
            if search:
                kill_re = re.compile(r'^url:\s?|\s+', re.IGNORECASE)
        elif self.ui.decl:
            self.url_re = re.compile(_declmidpat(), re.IGNORECASE|re.VERBOSE)
            if search:
                kill_re = re.compile(_nntppat(), re.IGNORECASE|re.VERBOSE)
        else:
            self.url_re = re.compile(r'(\b%s\b)' % _midpat(),
                                     re.IGNORECASE|re.VERBOSE)
        return kill_re

    def findurls(self, text):
        '''Conducts a search for urls in text.'''
        kill_re = self.urlobject() # compile url_re
        if self.ui.proto != 'mid':
            def wipepat():
                headers = ('received', 'references', 'message-id',
                           'in-reply-to', 'delivered-to', 'list-id', 'path',
                           'return-path', 'newsgroups', 'nntp-posting-host',
                           'xref', 'x-id', 'x-abuse-info', 'x-trace',
                           'x-mime-autoconverted')
                headers = r'(%s)' % '|'.join(headers)
                header = r'''
                    ^               # start of line
                    %s:             # header followed by colon &
                    .+              # greedy anything (but newline)
                    (               # 0 or more group
                      \n            #  newline followed by
                      [ \t]+        #  greedy spacetabs
                      .+            #  greedy anything
                    ) *?
                    ''' % headers
                return r'%s|%s' % (header, _declmidpat())

            wipe_re = re.compile(wipepat(),
                                 re.IGNORECASE|re.MULTILINE|re.VERBOSE)
            text = wipe_re.sub('', text)
            cpan = self.ui.configitem('net', 'cpan',
                                      default='ftp://ftp.cpan.org/pub/CPAN')
            ctan = self.ui.configitem('net', 'ctan',
                                      default='ftp://ftp.ctan.org/tex-archive')
            rawcan = r'C%sAN:\s*/?([a-zA-Z]+?)'
            for can in [(cpan, 'P'), (ctan, 'T')]:
                if can[0]:
                    cansub = r'%s/\1' % can[0].rstrip('/')
                    text = re.sub(rawcan % can[1], cansub, text)
        urls = [u[0] for u in self.url_re.findall(text)]
        if kill_re:
            urls = [kill_re.sub('', u) for u in urls]
        self.items += urls
        self.urlfilter()
        self.items.sort()
