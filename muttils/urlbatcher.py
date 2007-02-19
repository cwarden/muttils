# $Id$

###
# Caveat:
# If input is read from stdin, it should be of one type
# (text/plain, text/html, email) because the type detecting
# mechanism is only triggered once.
# However you should be able to run this on all kind of files,
# input is checked anew for each file.
###

import iterm, kiosk, pybrowser, ui, urlcollector, util
import os

class urlbatcher(urlcollector.urlcollector):
    '''
    Parses input for either web urls or message-ids.
    Browses all urls or creates a message tree in mutt.
    You can specify urls/ids by a regex pattern.
    '''
    options = {
            'proto': 'web',
            'decl': False,
            'pat': None,
            'kiosk': '',
            'browse': False,
            'local': False,
            'mhiers': '',
            'specdirs': '',
            'mask': None,
            'xb': False,
            'getdir': '',
            }

    def __init__(self, parentui=None, files=None, opts={}):
        urlcollector.urlcollector.__init__(self)
        self.ui = parentui or ui.config()
        self.files = files
        opts = util.checkmidproto(opts)
        self.options.update(opts.items())
        for k, v in self.options.iteritems():
            setattr(self, k, v)

    def urlgo(self):
        if self.proto == 'mid':
            opts = util.deletewebonlyopts(self.options)
            k = kiosk.kiosk(self.ui, items=self.items, opts=opts)
            k.kioskstore()
        elif self.getdir:
            util.goonline()
            os.execvp('wget', ['wget', '-P', self.getdir] + self.items)
        else:
            b = pybrowser.browser(parentui=self.ui,
                    items=self.items, xb=self.xb)
            b.urlvisit()
                    
    def urlsearch(self):
        if self.proto != 'mid':
            self.ui.updateconfig()
            self.cpan = self.ui.configitem('can', 'cpan')
            self.ctan = self.ui.configitem('can', 'ctan')
        self.urlcollect()
        if not self.files:
            it = iterm.iterm()
            it.terminit()
        if self.items:
            yorn = '%s\nretrieve the above %s? yes, [No] ' \
                    % ('\n'.join(self.items),
                       util.plural(len(self.items),
                           ('url', 'message-id')[self.proto=='mid']))
            if raw_input(yorn).lower() in ('y', 'yes'):
                self.urlgo()
        else:
            msg = 'no %ss found. [ok] ' % ('url',
                    'message-id')[self.proto=='mid']
            raw_input(msg)
        if not self.files:
            it.reinit()
