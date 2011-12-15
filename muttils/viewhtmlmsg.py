'''viewhtml - unpack html message and display with browser
'''

# $Id$

import email, email.Errors, email.Iterators, email.Utils
import os.path, re, shutil, sys, tempfile, time, urllib
from muttils import pybrowser, ui, util

class viewhtml(pybrowser.browser):
    def __init__(self, safe, keep, use_inotify, app, args):
        self.ui = ui.ui()
        self.ui.updateconfig()
        pybrowser.browser.__init__(self, parentui=self.ui,
                                   app=app, evalurl=True)
        self.inp = args
        self.safe = safe or self.ui.configbool('html', 'safe')
        self.keep = keep
        self.use_inotify = use_inotify or self.ui.configbool('html', 'inotify')
        if self.keep is None and not use_inotify:
            self.keep = self.ui.configint('html', 'keep', 3)

    def cleanup(self, tmpdir):
        if self.keep or self.use_inotify:
            shutil.rmtree(tmpdir)

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
            html = html.get_payload(decode=True)
            fc = 0
            for part in msg.walk():
                fc += 1
                fn = (part.get_filename() or part.get_param('filename') or
                      part.get_param('name', 'prefix_%d' % fc))
                if part['content-id']:
                    # safe ascii filename w/o spaces
                    fn = urllib.unquote(fn)
                    fn = fn.decode('ascii',
                                   'replace').encode('ascii', 'replace')
                    fn = fn.replace(' ', '_').replace('?', '-')
                    cid = email.Utils.unquote(part['content-id'])
                    html = html.replace('cid:%s' % cid, fn)
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
            if self.use_inotify:
                import inotifyx
                try:
                    fd = inotifyx.init()
                    wd = inotifyx.add_watch(fd, htmlfile, inotifyx.IN_CLOSE)
                    self.urlvisit()
                    # timeout after keep seconds, or wait forever if keep is None
                    if self.keep:
                        event = inotifyx.get_events(fd, self.keep)
                    else:
                        events = inotifyx.get_events(fd)
                    inotifyx.rm_watch(fd, wd)
                except IOError:
                    raise util.DeadMan('Failed to enable inotify.  Verify that /proc/sys/fs/inotify/max_user_watches is high enough.')
                finally:
                    os.close(fd)
            elif self.keep:
                self.urlvisit()
                time.sleep(self.keep)
        finally:
            self.cleanup(htmldir)
