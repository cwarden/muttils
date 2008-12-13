# $Id$

import urlcollector, urlregex
import iterm, kiosk, pybrowser, tpager, ui, util
import os.path

try:
    import readline
    loaded_readline = True
    confirm_prompt = '''
press <UP> or <C-P> to edit %(name)s,
<C-C> to cancel, <RET> to visit %(name)s:
%(url)s
'''
except ImportError:
    loaded_readline = False
    confirm_prompt = '''
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
        expando = {'name': self.name, 'url': self.items[0]}
        if loaded_readline:
            readline.clear_history()
            readline.add_history(self.items[0])
        url = self.rawinput(confirm_prompt % expando)
        if url:
            if loaded_readline:
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
        elif self.ui.getdir:
            self.ui.getdir = savedir(self.ui.getdir)
            cs = ['wget', '-P', self.ui.getdir]
        elif self.ui.proto == 'ftp' or urlregex.ftpcheck(url):
            if self.ui.ftpdir:
                # otherwise eventual download to cwd
                self.ui.ftpdir = savedir(self.ui.ftpdir)
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
        if not cs:
            b = pybrowser.browser(parentui=self.ui, items=self.items)
            b.urlvisit()
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
