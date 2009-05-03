# $Id$

'''viewhtml - unpack html message and display with browser
'''

from muttils import pybrowser, ui, util
import email, email.Errors, email.Iterators, email.Utils
import os.path, re, shutil, sys, tempfile, time, urllib

class viewhtml(pybrowser.browser):
    def __init__(self, parentui=None, inp='', safe=False, keep=None, app=''):
        self.ui = parentui or ui.ui()
        self.ui.updateconfig()
        pybrowser.browser.__init__(self, parentui=self.ui,
                                   app=app, evalurl=True)
        self.inp = inp
        self.safe = safe or self.ui.configbool('html', 'safe')
        self.keep = keep
        if self.keep is None:
            self.keep = self.ui.configint('html', 'keep', 3)

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
        if not msg or not msg['message-id']:
            raise util.DeadMan('input not a message')
        htiter = email.Iterators.typed_subpart_iterator(msg, subtype='html')
        try:
            html = htiter.next()
        except StopIteration:
            raise util.DeadMan('no html found')
        htmldir = tempfile.mkdtemp('', 'viewhtmlmsg.')
        try:
            htmlfile = os.path.join(htmldir, 'index.html')
            html = html.get_payload(decode=True)
            for part in msg.walk():
                fn = (part.get_filename() or 
                      part.get_param(param='filename') or
                      part.get_param(param='name'))
                if fn:
                    fn = urllib.unquote(fn)
                    # safe ascii filename w/o spaces
                    fn = fn.decode('ascii', 'replace').encode('ascii', 'replace')
                    fn = fn.replace(' ', '_').replace('?', '-')
                    if part['content-id']:
                        cid = email.Utils.unquote(part['content-id'])
                        html = html.replace('cid:%s' % cid, fn)
                    fp = open(os.path.join(htmldir, fn), 'wb')
                    fp.write(part.get_payload(decode=True))
                    fp.close()
            if self.safe:
                safe_pat = r'(src|background)\s*=\s*["\']??https??://[^"\'>]*["\'>]'
                html = re.sub(safe_pat, r'\1="#"', html)
            fp = open(htmlfile, 'wb')
            fp.write(html)
            fp.close()
            self.items = ['file://' + htmlfile]
            self.urlvisit()
            if self.keep:
                time.sleep(self.keep)
                shutil.rmtree(htmldir)
        except:
            # on error always remove personal mail
            shutil.rmtree(htmldir)
