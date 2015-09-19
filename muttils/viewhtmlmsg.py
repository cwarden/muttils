'''viewhtml - unpack html message and display with browser
'''

# $Id$

import email, email.Errors, email.Iterators, email.Utils
import os.path, re, shutil, sys, tempfile
from muttils import pybrowser, ui, util

try:
    import inotifyx
except ImportError:
    import time


class viewhtml(pybrowser.browser):
    def __init__(self, safe, keep, app, args):
        self.ui = ui.ui()
        self.ui.updateconfig()
        pybrowser.browser.__init__(self, parentui=self.ui,
                                   app=app, evalurl=True)
        self.inp = args
        self.safe = safe or self.ui.configbool('html', 'safe')
        self.keep = keep
        if self.keep is None:
            self.keep = self.ui.configint('html', 'keep', 3)

    def cleanup(self, tmpdir):
        if self.keep:
            shutil.rmtree(tmpdir)

    def ivisit(self):
        try:
            fd = inotifyx.init()
            wd = inotifyx.add_watch(fd, self.items[0], inotifyx.IN_CLOSE)
            self.urlvisit()
            inotifyx.get_events(fd, self.keep)
            inotifyx.rm_watch(fd, wd)
            os.close(fd)
        except IOError:
            hint = ('consider increasing '
                    '/proc/sys/fs/inotify/max_user_watches')
            raise util.DeadMan('failed to enable inotify', hint=hint)

    def view(self):
        try:
            if self.inp:
                if len(self.inp) > 1:
                    raise util.DeadMan('only 1 argument allowed')
                fp = open(self.inp[0], 'rb')
            else:
                fp = sys.stdin
            msg = email.message_from_file(fp)
            if self.inp:
                fp.close()
        except email.Errors.MessageParseError, inst:
            raise util.DeadMan(inst)
        if not msg:
            raise util.DeadMan('input not a message')
        if not msg['message-id']:
            hint = ('make sure input is a raw message,'
                    ' in mutt: unset pipe_decode')
            raise util.DeadMan('no message-id found', hint=hint)
        htiter = email.Iterators.typed_subpart_iterator(msg, subtype='html')
        try:
            html = htiter.next()
        except StopIteration:
            raise util.DeadMan('no html found')
        htmldir = tempfile.mkdtemp('', 'viewhtmlmsg.')
        try:
            htmlfile = os.path.join(htmldir, 'index.html')
            charset = html.get_param('charset')
            html = html.get_payload(decode=True)
            if charset:
                charsetmeta = '<meta charset="%s">' % charset
                if '<head>' in html:
                    html = html.replace('<head>', '<head>%s' % charsetmeta)
                else:
                    html = '<head>%s</head>%s' % (charsetmeta, html)
            fc = 0
            for part in msg.walk():
                fc += 1
                fn = (part.get_filename() or part.get_param('filename') or
                      part.get_param('name', 'prefix_%d' % fc))
                if part['content-id']:
                    # safe ascii filename: replace it with cid
                    fn = email.Utils.unquote(part['content-id'])
                    html = html.replace('"cid:%s"' % fn, "%s" % fn)
                fpay = part.get_payload(decode=True)
                if fpay:
                    fp = open(os.path.join(htmldir, fn), 'wb')
                    fp.write(fpay)
                    fp.close()
            if self.safe:
                spat = r'(src|background)\s*=\s*["\']??https??://[^"\'>]*["\'>]'
                html = re.sub(spat, r'\1="#"', html)
            fp = open(htmlfile, 'wb')
            fp.write(html)
            fp.close()
            self.items = [htmlfile]
            if self.keep:
                try:
                    self.ivisit()
                except NameError:
                    self.urlvisit()
                    time.sleep(self.keep)
            else:
                self.urlvisit()
        finally:
            self.cleanup(htmldir)
