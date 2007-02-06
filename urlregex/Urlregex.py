# $Id$

from urlregex.Urlparser import Urlparser, UrlparserError
import re

def mkDomPat(top, valid, delim):
    '''Creates the raw domain parts of the url patterns.
    2 patterns, the second of which contains spaces.'''
    dom = r'''
        %(top)s             # top level preceded by dot
        (                   # { ungreedy 0 or more
            (/|:\d+)        #   slash or port
            [%(valid)s] *?  #   0 or more valid  
        ) ?                 # } 0 or one
        (?=                 # look-ahead non-consumptive assertion
            [%(delim)s] *?  #  either 0 or more punctuation
            [^%(valid)s]    #  followed by a non-url char
        |                   # or else
            $               #  then end of the string
        )
        ''' % vars()
    spdom = r'''
        %(top)s              # top level dom preceded by dot
        (                    # { 0 or more
            \s*?/            #   opt space and slash
            [%(valid)s\s] *? #   valid or space (space to be removed)
        ) ?                  # } 0 or one
        (?=>)                # lookahead for '>'
        ''' % vars()
    return dom, spdom

# and now to the url parts
valid = r'-._a-z0-9/#~:,;?+=&%!()@' # valid url-chars+comma+semicolon+parenthesises+@
                                    # @: filtered with webCheck, false positives with
                                    # che@*blacktrash.org* otherwise
                                    # Message-ID: <10rb6mngqccs018@corp.supernews.com>
                                    # Message-id: <20050702131039.GA10840@oreka.com>
                                    # Message-ID: <e2jctg$kgp$1@news1.nefonline.de>
idy = r'-._a-z0-9#~?+=&%!$\]['      # valid message-id-chars ### w/o ':/'?
delim = r'-.,:?!)('                 # punctuation (how 'bout '!'?)

# generic domains
generics = [
        'aero', 'arpa', 'biz', 'cat', 'com', 'coop',
        'edu', 'gov', 'info', 'int', 'jobs', 'mil', 'mobi', 'museum',
        'name', 'net', 'org', 'pro', 'travel'
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

top = r'\.(%s)' % '|'.join(tops)
generic = r'\.(%s)' % '|'.join(generics)

proto_dom, proto_spdom = mkDomPat(top, valid, delim)
any_dom, any_spdom = mkDomPat(generic, valid, delim)

#CPAN = 'ftp://ftp.cpan.org/pub/CPAN/'
CPAN = r'ftp://ftp.rz.ruhr-uni-bochum.de/pub/CPAN/\1'
#CTAN = 'ftp://ftp.ctan.org/tex-archive/'
CTAN = r'ftp://ftp.dante.de/tex-archive/\1'

# get rid of *quoted* mail headers of no use
# (how to do this more elegantly?)
headers = [
        'Received', 'References', 'Message-ID', 'In-Reply-To',
        'Delivered-To', 'List-Id', 'Path', 'Return-Path',
        'Newsgroups', 'NNTP-Posting-Host',
        'Xref', 'X-ID', 'X-Abuse-Info', 'X-Trace', 'X-MIME-Autoconverted'
        ]
head = '|'.join(headers)

headsoff = r'''
    (\n|^)          # newline or very start
    %s:             # header followed by colon &
    .+              # greedy anything (but newline)
    (               # { 0 or more
        \n          #   newline followed by
        [ \t]+      #   greedy spacetabs
        .+          #   greedy anything
    ) *?            # } 0 or more
    ''' % head

# attributions:
nproto = '(msgid|news|nntp|message(-id)?|article|MID)(:\s*|\s+)<{,2}'

mid = r'''
    [%(idy)s] +?    # one or more valid id char
    @
    [-._a-z0-9] +?  # one or more server char
    %(top)s         # top level domain
    \b
    ''' % vars()

declid = r'(%(nproto)s%(mid)s)' % vars()
simplid = r'(\b%(mid)s)' % vars()

rawwipe = r'(%(declid)s)|(%(headsoff)s)' % vars()

## precompiled regexes ##
ftp_re = re.compile(r'(s?ftp://|ftp\.)', re.IGNORECASE)

address = '[-._a-z0-9]+@[-._a-z0-9]+%s' % top
mail = r'''
    \b(                 # word boundary and group open
        mailto:
        %(address)s     # address
        \?subject=      # ?subject=
        [^>]            # any except >
    |                   # or
        (mailto:)?      # optional mailto
        %(address)s     # and address
    )\b                 # close group and word boundary
    ''' % vars()
mail_re = re.compile(mail, re.IGNORECASE|re.VERBOSE)
    
## filter functions ##

def webCheck(url):
    return not mail_re.match(url)

def ftpCheck(url):
    return ftp_re.match(url)

def httpCheck(url):
    return not mail_re.match(url) and not ftp_re.match(url)

def mailCheck(url):
    return mail_re.match(url)

filterdict = { 'web':    webCheck,
               'ftp':    ftpCheck,
               'http':   httpCheck,
               'mailto': mailCheck }


class UrlregexError(Exception):
    '''Exception class for the Urlregex module.'''

class Urlregex(Urlparser):
    '''
    Provides functions to extract urls from text,
    customized by attributes.
    Detects also www-urls that don't start with a protocol
    and urls spanning more than 1 line
    if they are enclosed in '<>'.
    '''
    def __init__(self, proto='all', decl=False, uniq=True):
        Urlparser.__init__(self, proto=proto) # <- items, url_re
        self.decl = decl        # list only declared urls
        self.uniq = uniq        # list only unique urls
        self.kill_re = None     # customized pattern to find non url chars
        self.intro = ''
        self.protocol = ''      # pragmatic proto (may include www., ftp.)
        self.proto_re = None

    def setStrings(self):
        ### intro ###
        if self.proto in ('all', 'web'): ## groups
            # list protocols
            protocols = [ r'(www|ftp)\.', 
                          r'https?://', r's?ftp://', r'gopher://',
                          r'mailto:' ]
            # finger, telnet, whois, wais?
            if self.proto == 'web':
                protocols = protocols[:4] # http, ftp, gopher
            intros = r'%s' % '|'.join(protocols)
            decl_protos = r'%s' % '|'.join(protocols[1:]) # w/o (www|ftp)\.
            self.intro = r'(%s)' % intros
            self.protocol = r'(%s)' % decl_protos

        else:                  ## singles
            self.decl = True
            self.protocol = '%s://' % self.proto
            if self.proto == 'http':
                self.intro = r'(https?://|www\.)'
            elif self.proto == 'ftp':
                self.intro = r'(s?ftp://|ftp\.)'
            else:
                self.intro = self.protocol
        self.intro = r'(url:)?%s' % self.intro

    def getRaw(self):

        proto_url = r'''     ## long url ##
            (?<=<)           # look behind for '<'
            %(intro)s        # intro
            [%(valid)s\s] +? # valid or space (space to be removed)
            %(spdom)s        # dom w/ spaces
            |                ## or url in 1 line ##
            \b               # start at word boundary
            %(intro)s        # intro
            [%(valid)s] +?   # followed by 1 or more valid url char
            %(dom)s          # dom
            ''' % { 'intro': self.intro,
                    'valid': valid,
                    'spdom': proto_spdom,
                    'dom':   proto_dom }

        proto_pat = (r'(%s|%s)' % (mail, proto_url),
                r'(%s)' % proto_url)[self.proto!='all']

        ## follows an attempt to comprise as much urls as possible
        ## some bad formatted stuff too
        any_url = r'''       ## long url ##
            (?<=<)           # look behind for '<'
            [%(valid)s\s] +? # valid or space (space to be removed)
            %(spdom)s        # dom w/ spaces
            |                ## or url in 1 line ##
            \b               # start at word boundary
            [%(valid)s] +?   # one or more valid characters
            %(dom)s          # dom
            ''' % { 'valid': valid,
                    'spdom': any_spdom,
                    'dom':   any_dom }
        
        any_pat = (r'(%s|%s|%s)' % (mail, proto_url, any_url),
                r'(%s|%s)' % (proto_url, any_url))[self.proto!='all']
        return (any_pat, proto_pat)[self.decl]

    def uniDeluxe(self):
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

    def urlFilter(self):
        if not self.decl and self.proto in filterdict:
            self.items = filter(filterdict[self.proto], self.items)
        if self.uniq:
            self.items = list(set(self.items))
            if self.proto != 'mid' and not self.decl:
                self.uniDeluxe()

    def urlObjects(self, search=True):
        '''Creates customized regex objects of url.'''
        try:
            self.protoTest()
        except UrlparserError, e:
            raise UrlregexError(e)
        if self.proto == 'mailto':# be pragmatic and list not only declared
            self.url_re = mail_re
            self.proto_re = re.compile(r'^mailto:')
        elif self.proto != 'mid':
            self.setStrings()
            rawurl = self.getRaw()
            self.url_re = re.compile(rawurl, re.IGNORECASE|re.VERBOSE)
            if search:
                self.kill_re = re.compile(r'\s+?|^url:', re.IGNORECASE)
            if not self.decl:
                self.proto_re = re.compile(r'^%s' % self.protocol,
                        re.IGNORECASE)
        elif self.decl:
            self.url_re = re.compile(declid, re.IGNORECASE|re.VERBOSE)
            if search:
                self.kill_re = re.compile(nproto, re.I)
        else:
            self.url_re = re.compile(simplid, re.IGNORECASE|re.VERBOSE)

    def findUrls(self, data):
        '''Conducts a search for urls in data.
        Data is supposed to be text but tested whether
        it's a message/Mailbox (then passed to Urlparser).'''
        self.urlObjects() # compile url_re
        s = self.mailDeconstructor(data)
        if self.proto != 'mid':
            wipe_resub = re.compile(rawwipe, re.IGNORECASE|re.VERBOSE), ''
            cpan_resub = re.compile(r'CPAN:\s*/?([A-Za-z]+?)'), CPAN 
            ctan_resub = re.compile(r'CTAN:\s*/?([A-Za-z]+?)'), CTAN
            for resub in (wipe_resub, cpan_resub, ctan_resub):
                s = resub[0].sub(resub[1], s)
        urls = [u[0] for u in self.url_re.findall(s)]
        if self.kill_re:
            urls = [self.kill_re.sub('', u) for u in urls]
        if urls:
            self.items += urls
        self.urlFilter()
