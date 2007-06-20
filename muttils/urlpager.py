# $Id$

import urlcollector, urlregex
import conny, iterm, kiosk, pybrowser, tpager, ui, util
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
    def __init__(self, parentui=None, files=None, opts={}):
        self.ui = parentui or ui.ui()
        self.ui.updateconfig()
        self.ui.resolveopts(opts)
        urlcollector.urlcollector.__init__(self, self.ui, files=files)
        tpager.tpager.__init__(self, self.ui, name='url')

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
        return (self.ui.proto == 'mailto'
                or self.ui.proto == 'all' and urlregex.mailcheck(self.items[0]))

    def msgretrieval(self):
        '''Passes message-id and relevant options to kiosk.'''
        k = kiosk.kiosk(self.ui, items=self.items)
        k.kioskstore()

    def urlgo(self, mail=False):
        url, cs, conn, cwd = self.items[0], [], True, None
        if mail:
            cs = [self.ui.configitem('messages', 'mailer')]
            conn = False
        elif self.ui.getdir:
            self.ui.getdir = savedir(self.ui.getdir)
            cs = ['wget', '-P', self.ui.getdir]
        elif self.ui.proto == 'ftp' or urlregex.ftpcheck(url):
            if self.ui.ftpdir:
                # otherwise eventual download to cwd
                self.ui.ftpdir = savedir(self.ui.ftpdir)
                cwd = os.getcwdu()
                os.chdir(self.ui.ftpdir)
            cs = [self.ui.configitem('net', 'ftpclient')]
            # for ftp programs that have more of a browser interface
            # we assume a file if url has a file extension
            assumefile = os.path.splitext(url)[1]
            if cs[0].endswith('lftp') and assumefile:
                # lftp need optional command
                cs += ['-c', 'get']
            elif cs[0].endswith('ncftp') and assumefile:
                # use ncftpget instead
                cs = ['%sget' % cs[0]]
        if not cs:
            b = pybrowser.browser(parentui=self.ui,
                                  items=self.items, app=self.ui.app)
            b.urlvisit()
        else:
            if conn:
                conny.goonline(self.ui)
            cs += [url]
            util.systemcall(cs)
        if cwd:
            os.chdir(cwd)

    def urlsel(self):
        name = self.name
        self.name = 'unique %s' % name
        # as there is no ckey, interact() returns always 0
        self.interact()
        if not self.items:
            return
        if self.ui.proto == 'mid':
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
        if self.ui.proto == 'mid':
            self.name = 'message-id'
        elif self.ui.proto != 'all':
            self.name = '%s %s' % (self.ui.proto, self.name)
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
                if self.items and self.ui.proto != 'mid':
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
