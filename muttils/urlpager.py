# $Id$

import iterm, kiosk, pybrowser, tpager, ui, urlcollector, util
from urlregex import mailcheck, ftpcheck
import os, readline

readline_prompt = '''
press <UP> or <C-P> to edit %(name)s,
<C-C> to cancel, <RET> to visit %(name)s:
%(url)s
'''

edit_prompt = '''
press <RET> to visit %(name)s, <C-C> to cancel,
or enter %(name)s manually:
%(url)s
'''


class urlpager(urlcollector.urlcollector, tpager.tpager):
    options = {
            'proto': 'all',
            'decl': False,
            'pat': None,
            'midrelax': False,
            'kiosk': '',
            'browse': False,
            'local': False,
            'news': False,
            'mhiers': '',
            'specdirs': '',
            'mask': None,
            'xb': False,
            'tb': False,
            'ftp': 'ftp',
            'getdir': '',
            }

    def __init__(self, parentui=None, files=None, opts={}):
        urlcollector.urlcollector.__init__(self)
        tpager.tpager.__init__(self, name='url')
        self.ui = parentui or ui.config()
        self.files = files
        self.options.update(opts.items())
        self.options = util.checkmidproto(self.options)
        for k, v in self.options.iteritems():
            setattr(self, k, v)

    def urlconfirm(self):
        if not self.files:
            url = raw_input(edit_prompt %
                    {'name': self.name, 'url': self.items[0]})
        else:
            readline.add_history(self.items[0])
            url = raw_input(readline_prompt %
                    {'name': self.name, 'url': self.items[0]})
        if url:
            self.items = [url]

    def mailcondition(self):
        '''Return True if mail client should be called.'''
        return (self.proto == 'mailto'
                or self.proto == 'all' and mailcheck(self.items[0]))

    def msgretrieval(self):
        '''Passes message-id and relevant options to kiosk.'''
        opts = util.deletewebonlyopts(self.options)
        k = kiosk.kiosk(self.ui, items=self.items, opts=opts)
        k.kioskstore()

    def urlgo(self, mail=False):
        url, cs, conny = self.items[0], [], True
        if mail:
            self.ui.updateconfig()
            cs = [self.ui.configitem('messages', 'mailer')]
            conny = False
        elif self.getdir:
            cs = ['wget', '-P', self.getdir]
        elif self.proto == 'ftp' or ftpcheck(url):
            if not os.path.splitext(url)[1] and not url.endswith('/'):
                self.items = [url + '/']
            cs = [self.ftp]
        if not cs:
            b = pybrowser.browser(parentui=self.ui,
                    items=self.items, tb=self.tb, xb=self.xb)
            b.urlvisit()
        else:
            cs += [url]
            if conny:
                util.goonline()
            if not os.isatty(0): # not connected to terminal
                tty = os.ctermid()
                cs += ['<', tty, '>', tty]
                os.system(' '.join(cs))
            else:
                os.execvp(cs[0], cs)

    def urlsel(self):
        name = self.name
        self.name = 'unique %s' % name
        # as there is no ckey, interact() returns always 0
        self.interact()
        if not self.items:
            return
        if self.proto == 'mid':
            self.msgretrieval(self)
        elif self.mailcondition():
            # mail client allows editing of address
            self.urlgo(mail=True)
        else:
            self.name = name
            try:
                if not self.files:
                    it = iterm.iterm()
                    it.terminit()
                self.urlconfirm()
                if not self.files:
                    it.reinit()
                self.urlgo()
            except KeyboardInterrupt:
                pass

    def midyorn(self):
        yorn = raw_input('retrieve message-id <%s>? Yes [No] ' % self.items[0])
        if yorn.lower() in ('y', 'yes'):
            self.msgretrieval()
        self.items = None

    def urlsearch(self):
        if self.proto != 'mid':
            self.ui.updateconfig()
            self.cpan = self.ui.configitem('can', 'cpan')
            self.ctan = self.ui.configitem('can', 'ctan')
            if self.proto != 'all':
                self.name = '%s %s' % (self.proto, self.name)
        else:
            self.name = 'message-id'
        self.urlcollect()
        ilen = len(self.items)
        if len(self.items) > 1:
            self.urlsel()
        elif self.items and self.mailcondition():
            # mail client allows editing of address
            self.urlgo(mail=True)
        else:
            try:
                if not self.files:
                    it = iterm.iterm()
                    it.terminit()
                if self.items and self.proto != 'mid':
                    self.urlconfirm()
                elif self.items: # proto == 'mid'
                    self.midyorn()
                else:
                    raw_input('no %ss found [ok] ' % self.name)
                if not self.files:
                    it.reinit()
                if self.items:
                    self.urlgo()
            except KeyboardInterrupt:
                pass
