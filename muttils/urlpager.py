# $Id$

import os.path
try:
    import readline
    loadedreadline = True
except ImportError:
    loadedreadline = False

from muttils import urlcollector, urlregex
from muttils import iterm, kiosk, pybrowser, tpager, ui, util, wget

class urlpager(urlcollector.urlcollector, tpager.tpager):
    def __init__(self, parentui=None, files=None, opts={}):
        self.ui = parentui or ui.ui()
        self.ui.updateconfig()
        self.ui.resolveopts(opts)
        self.mailer = self.ui.configitem('messages', 'mailer', default='mutt')
        urlcollector.urlcollector.__init__(self, self.ui, files=files)
        tpager.tpager.__init__(self, self.ui, name='url')

    def rawinput(self, prompt):
        '''Wraps raw_input in interactive terminal if needed.'''
        if not self.files:
            it = iterm.iterm()
            it.terminit()
        answer = raw_input(prompt)
        if not self.files:
            it.reinit()
        return answer

    def urlconfirm(self):
        action = not self.ui.getdir and 'visit' or 'download'
        expando = {'name': self.name, 'act': action, 'url': self.items[0]}
        if loadedreadline:
            readline.clear_history()
            readline.add_history(self.items[0])
            prompt = ('press <UP> or <C-P> to edit %(name)s,\n'
                      '<C-C> to cancel, <RET> to %(act)s %(name)s:\n')
        else:
            prompt = ('press <RET> to %(act)s %(name)s, <C-C> to cancel,\n'
                      'or enter %(name)s manually:\n')
        url = self.rawinput((prompt + '%(url)s\n') % expando)
        if url:
            if loadedreadline:
                readline.clear_history()
            self.items = [url]

    def msgretrieval(self):
        '''Passes message-id and relevant options to kiosk.'''
        yorn = self.rawinput('retrieve message-id <%s>? yes [No] '
                             % self.items[0])
        if yorn.lower() in ('y', 'yes'):
            k = kiosk.kiosk(self.ui, items=self.items)
            k.kioskstore()

    def urlretrieval(self, mail):
        url, cs, cwd = self.items[0], [], ''
        if mail:
            cs = [self.mailer]
        elif self.ui.proto == 'ftp' or urlregex.ftpcheck(url):
            if self.ui.ftpdir:
                # otherwise eventual download to cwd
                self.ui.ftpdir = util.savedir(self.ui.ftpdir)
                cwd = os.getcwdu()
                os.chdir(self.ui.ftpdir)
            cs = [self.ui.configitem('net', 'ftpclient', default='ftp')]
            # for ftp programs that have more of a browser interface
            # we assume a file if url has a file extension
            assumefile = os.path.splitext(url)[1]
            if cs[0].endswith('lftp') and assumefile:
                # lftp needs an optional command
                cs += ['-c', 'get']
            elif cs[0].endswith('ncftp') and assumefile:
                # use ncftpget instead
                cs = ['%sget' % cs[0]]
        if not cs and not self.ui.getdir:
            b = pybrowser.browser(parentui=self.ui, items=self.items)
            b.urlvisit()
        elif self.ui.getdir:
            uget = wget.wget(self.ui)
            uget.download([url])
        else:
            cs += [url]
            util.systemcall(cs)
        if cwd:
            os.chdir(cwd)

    def urlselect(self):
        if self.ui.proto == 'mid':
            self.name = 'message-id'
        elif self.ui.proto != 'all':
            self.name = '%s %s' % (self.ui.proto, self.name)
        self.urlcollect()
        if not self.items:
            self.rawinput('no %ss found [ok] ' % self.name)
            return
        if len(self.items) > 1:
            name = self.name
            self.name = 'unique %s' % name
            # as there is no ckey, interact() returns always 0
            self.interact()
            self.name = name
        if not self.items:
            return
        mail = (self.ui.proto == 'mailto' or
                self.ui.proto == 'all' and urlregex.mailcheck(self.items[0]))
        try:
            if self.ui.proto == 'mid':
                self.msgretrieval()
            elif mail and self.mailer != 'mail':
                # mail client allows editing of address
                self.urlretrieval(mail)
            else:
                self.urlconfirm()
                if self.items:
                    self.urlretrieval(mail)
        except KeyboardInterrupt:
            pass
