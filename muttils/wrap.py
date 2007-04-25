# $Id$

import util
import re, sys

empty_re = re.compile(r'\s+$', re.MULTILINE)
ind_re = re.compile(r'\s+', re.MULTILINE)
wbreak_re = re.compile(r'\b[-/]+\b')
tail_re = re.compile(r'\w[-/([{&^]$')

def mrex(pat):
    '''Checks and returns MULTILINE regex of pat.'''
    try:
        return re.compile(r'%s' % pat, re.MULTILINE)
    except re.error, inst:
        raise util.DeadMan("error in pattern `%s': %s" % (pat, inst))

def unmangle(mobj):
    '''Returns line with >[fF]rom unmangled, taking quotes into account.'''
    if mobj.group(1):
        return '%s%s' % (mobj.group(1), mobj.group(2)[1:])
    return mobj.group(2)[1:]

class wrap(object):
    '''
    Provides customized line breaking.
    Initialize with arguments of your choice,
    run formwrap to retrieve list of formatted lines.
    Lines are broken at hyphens in words too;
    if you didn't exclude blanks from wrapping,
    a blank indent starts a new paragraph;
    quoted lines are wrapped if you specified quote chars.
    Example:
    wrap.py -Q -e '|' -w 72
    wraps email style quoted lines
    but leaves lines starting with '|' untouched.
    '''
    def __init__(self, inp=None, opts={}):
        self.input = inp or None # will be treated according to type
        self.width = 0           # default wrap width
        self.ipar = 0            # wrap width,
                                 # starting new par with each indent change
        self.respect = 0         # wrap width respecting line breaks
        self.tabwidth = 8        # width of a tab in spaces
        self.excl = ''           # exclude lines matching pattern excl from wrapping
        self.quote = ''          # treat lines starting with chars quote as quoted
        self.hyph = False        # break words at hyphens
        self.qmail = False       # treat as email, ">" (additional quote char)
        self.email = False       # treat as email: skip headers, unmangle >From
        self._outfunc = False    # output as stream
        for k in opts.iterkeys():
            setattr(self, k, opts[k])
        # wrap width falls back on width if neither respect nor ipar
        # are specified in that order, and finally to 78
        self.defwidth = self.width = (
                self.respect or self.ipar or self.width or 78)
        if self.excl:
            self.excl = mrex(self.excl)
        if self.qmail:
            self.email = True
            if '>' not in self.quote:
                self.quote = '>%s' % self.quote
        del self.qmail
        if self.email and '>' in self.quote:
            self.email = mrex('([%s] ?)*(>[fF]rom)' % self.quote)
        elif self.email:
            self.email = mrex('([>%s] ?)*(>[fF]rom)' % self.quote)
        if self.quote:
            self.quote = mrex('([%s] ?)+' % self.quote)
        if self._outfunc:
            self._outfunc = self.streamout
        else:
            self._outfunc = self.collectout
        # attribs for internal use:
        self.olines = []         # output lines
        self.line = ''           # current line
        self.words = []          # current list of words to fill line
        self.holdspace = []      # current list of words in line
        self.hslen = 0           # len of current words as string
        self.indent = ''         # current indent
        self.qindent = ''        # current quote indent

    def streamout(self, line):
        '''Immediate print of wrapped line.'''
        sys.stdout.write(line)

    def collectout(self, line):
        '''Collects wrapped lines. Slightly faster.'''
        self.olines.append(line)

    def addholdspace(self):
        '''Ships out and resets holdspace.'''
        if self.holdspace:
            self._outfunc(self.qindent + self.indent
                    + ' '.join(self.holdspace) + '\n')
            self.holdspace = []

    def addoversize(self):
        '''Ships out holdspace and pops overlong word from list.'''
        self.addholdspace()
        self._outfunc(self.qindent + self.indent + self.words.pop(0) + '\n')

    def breakword(self, word, wlen):
        '''Tries to break word at hyphen(s).'''
        # what.a//bull-shit!
        frags = wbreak_re.split(word)
        # ['what','a','bull','shit!']
        fraglen = len(frags)
        if fraglen == 1 and wlen >= self.width:
            self.addoversize()
        elif fraglen > 1:
            fragtails = wbreak_re.findall(word) + ['']
            # -> ['.','//','-','']
            frags = [ft[0] + ft[1] for ft in zip(frags, fragtails)]
            # -> ['what.','a//','bull-','shit!']
            fragspace = []
            while frags:
                fraglen = len(''.join(fragspace + [frags[0]]))
                if self.hslen + fraglen <= self.width:
                    fragspace.append(frags.pop(0))
                else:
                    break
            if fragspace:
                self.holdspace.append(''.join(fragspace))
                self.words[0] = ''.join(frags)
            elif len(frags[0]) >= self.width:
                self.addholdspace()
                self.holdspace = [frags.pop(0)]
                self.words[0] = ''.join(frags)

    def breakline(self):
        self.words = self.line.split()
        if (self.hyph
                and self.holdspace
                and self.words[0] not in ('und', 'oder', 'bzw.')
                and tail_re.search(self.holdspace[-1], -2)):
            self.words[0] = self.holdspace.pop()+self.words[0]
        while self.words:
            self.hslen = len(' '.join(self.holdspace))
            word = self.words[0]
            wlen = len(word)
            if not self.hyph and wlen >= self.width:
                self.addoversize()
            elif self.hslen + wlen >= self.width:
                if self.hyph:
                    self.breakword(word, wlen)
                self.addholdspace()
            else:
                self.holdspace.append(self.words.pop(0))

    def getindent(self, regex):
        '''Returns indent string (quote or "normal" indent).'''
        indent = regex.match(self.line)
        if not indent:
            return ''
        return indent.group(0)

    def lineparser(self):
        # look for quote string
        if self.quote:    # and set quote indent
            qindent = self.getindent(self.quote)
            # if quote indent changed start a new line
            if qindent != self.qindent:
                self.addholdspace()
                self.qindent = qindent
                self.width = self.defwidth - len(qindent)
            if self.qindent:
                self.line = self.line.replace(self.qindent, '', 1)
        # check if line must go intact
        # mark: this way, if you have '>' as quote and exclude '|'
        # a line starting with '> |' will be left intact
        if (empty_re.match(self.line)
                or self.excl and self.excl.match(self.line)):
            self.addholdspace()
            self._outfunc(self.qindent + self.line)
            self.indent = ''
            self.width = self.defwidth - len(self.qindent)
        else:
            indent = self.getindent(ind_re)
            # hanging indent? (indent > self.indent)
            indchange = indent != self.indent
            if indchange and self.ipar or self.respect:
                self.addholdspace()
            if indchange:
                self.width = (self.defwidth - len(self.qindent)
                        - len(indent.replace('\t', ' ' * self.tabwidth)))
                self.indent = indent
            self.breakline() # and wrap

    def nowrap(self, lit):
        '''Puts out lines unwrapped while they are not empty.'''
        while self.line[:-1]:
            self._outfunc(self.line)
            self.line = lit.next()

    def literator(self, lit):
        '''Iterates over lines of file object.'''
        try:
            skipheaders = self.email
            while True:
                self.line = lit.next()
                sigsep = self.line == '-- \n'
                if skipheaders or sigsep:
                    if sigsep:
                        self.addholdspace()
                    self.nowrap(lit)
                    skipheaders = False
                if self.email:
                    self.line = self.email.sub(unmangle, self.line, 1)
                self.lineparser()
        except StopIteration:
            self.addholdspace()

    def formwrap(self):
        '''Checks excluding regexes and passes data to iterator.'''
        for i in self.defwidth, self.tabwidth:
            if not isinstance(i, int):
                raise util.DeadMan('integer expected, got "%s"' % i)
        if isinstance(self.input, list): # list of files
            for f in self.input:
                lit = open(f)
                try:
                    self.literator(lit)
                finally:
                    lit.close()
        else:
            if self.input is None:
                lit = sys.stdin
            else:
                lit = iter(self.input.splitlines(True))
            self.literator(lit)
