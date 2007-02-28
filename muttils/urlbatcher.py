# $Id$

###
# Caveat:
# If input is read from stdin, it should be of one type
# (text/plain, text/html, email) because the type detecting
# mechanism is only triggered once.
# However you should be able to run this on all kind of files,
# input is checked anew for each file.
###

import conny, iterm, kiosk, pybrowser, ui, urlcollector, util

class urlbatcher(urlcollector.urlcollector):
    '''
    Parses input for either web urls or message-ids.
    Browses all urls or creates a message tree in mutt.
    You can specify urls/ids by a regex pattern.
    '''
    defaults = {
            'proto': 'web',
            'decl': False,
            'pat': None,
            'kiosk': '',
            'browse': False,
            'news': False,
            'local': False,
            'mhiers': '',
            'specdirs': '',
            'mask': None,
            'app': '',
            'getdir': '',
            }

    def __init__(self, parentui=None, files=None, opts={}):
        urlcollector.urlcollector.__init__(self)
        self.ui = parentui or ui.config()
        self.ui.updateconfig()
        self.files = files
        util.resolveopts(self, opts)

    def urlgo(self):
        if self.proto == 'mid':
            k = kiosk.kiosk(self.ui, items=self.items, opts=self.defaults)
            k.kioskstore()
        elif self.getdir:
            conny.goonline(self.ui)
            util.systemcall(['wget', '-P', self.getdir] + self.items)
        else:
            b = pybrowser.browser(parentui=self.ui,
                    items=self.items, app=self.app)
            b.urlvisit()
                    
    def urlsearch(self):
        if self.proto != 'mid':
            self.cpan = self.ui.configitem('net', 'cpan')
            self.ctan = self.ui.configitem('net', 'ctan')
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
