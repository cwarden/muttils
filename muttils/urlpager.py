# $Id$

import conny, iterm, kiosk, pybrowser, tpager, ui, urlcollector, urlregex, util
import os.path, readline

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

def savedir(directory):
    '''Returns absolute path of directory if it is one.'''
    directory = util.absolutepath(directory)
    if not os.path.isdir(directory):
        raise util.DeadMan('%s: not a directory' % directory)
    return directory

class urlpager(urlcollector.urlcollector, tpager.tpager):
    defaults = {
            'proto': 'all',
            'decl': False,
            'pat': None,
            'kiosk': '',
            'browse': False,
            'local': False,
            'news': False,
            'mhiers': '',
            'specdirs': '',
            'mask': None,
            'app': '',
            'ftpdir': '',
            'getdir': '',
            }

    def __init__(self, parentui=None, files=None, opts={}):
        urlcollector.urlcollector.__init__(self)
        self.ui = parentui or ui.ui()
        tpager.tpager.__init__(self, self.ui, name='url')
        self.ui.updateconfig()
        self.files = files
        util.resolveopts(self, opts)

    def urlconfirm(self):
        expando = {'name': self.name, 'url': self.items[0]}
        if not self.files:
            url = raw_input(edit_prompt % expando)
        else:
            readline.add_history(self.items[0])
            url = raw_input(readline_prompt % expando)
        if url:
            self.items = [url]

    def mailcondition(self):
        '''Return True if mail client should be called.'''
        return (self.proto == 'mailto'
                or self.proto == 'all' and urlregex.mailcheck(self.items[0]))

    def msgretrieval(self):
        '''Passes message-id and relevant options to kiosk.'''
        k = kiosk.kiosk(self.ui, items=self.items, opts=self.defaults)
        k.kioskstore()

    def urlgo(self, mail=False):
        url, cs, conn = self.items[0], [], True
        if mail:
            cs = [self.ui.configitem('messages', 'mailer')]
            conn = False
        elif self.getdir:
            self.getdir = savedir(self.getdir)
            cs = ['wget', '-P', self.getdir]
        elif self.ftpdir:
            self.ftpdir = savedir(self.ftpdir)
            wd = os.getcwdu()
            os.chdir(self.ftpdir)
            if not os.path.splitext(url)[1] and not url.endswith('/'):
                self.items = [url + '/']
            cs = [self.ui.configitem('net', 'ftpclient')]
        if not cs:
            b = pybrowser.browser(parentui=self.ui,
                    items=self.items, app=self.app)
            b.urlvisit()
        else:
            if conn:
                conny.goonline(self.ui)
            cs += [url]
            util.systemcall(cs)
        if self.ftpdir:
            os.chdir(wd)

    def urlsel(self):
        name = self.name
        self.name = 'unique %s' % name
        # as there is no ckey, interact() returns always 0
        self.interact()
        if not self.items:
            return
        if self.proto == 'mid':
            self.msgretrieval()
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
        yorn = raw_input('retrieve message-id <%s>? yes [No] ' % self.items[0])
        if yorn.lower() in ('y', 'yes'):
            self.msgretrieval()
        self.items = None

    def urlsearch(self):
        if self.proto != 'mid':
            self.cpan = self.ui.configitem('net', 'cpan')
            self.ctan = self.ui.configitem('net', 'ctan')
            if self.proto != 'all':
                self.name = '%s %s' % (self.proto, self.name)
        else:
            self.name = 'message-id'
        self.urlcollect()
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
