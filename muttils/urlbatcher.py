# $Id$

###
# Caveat:
# If input is read from stdin, it should be of one type
# (text/plain, text/html, email) because the type detecting
# mechanism is only triggered once.
# However you should be able to run this on all kind of files,
# input is checked anew for each file.
###

import iterm, kiosk, pybrowser, ui, urlcollector, util, wget

class urlbatcher(urlcollector.urlcollector):
    '''
    Parses input for either web urls or message-ids.
    Browses all urls or creates a message tree in mutt.
    You can specify urls/ids by a regex pattern.
    '''
    def __init__(self, parentui=None, files=None, opts={}):
        self.ui = parentui or ui.ui()
        self.ui.updateconfig()
        self.ui.resolveopts(opts)
        urlcollector.urlcollector.__init__(self, self.ui, files=files)

    def urlgo(self):
        if self.ui.proto == 'mid':
            k = kiosk.kiosk(self.ui, items=self.items)
            k.kioskstore()
        elif self.ui.getdir:
            uget = wget.wget(self.ui)
            uget.download(self.items)
        else:
            b = pybrowser.browser(parentui=self.ui, items=self.items)
            b.urlvisit()
                    
    def urlsearch(self):
        self.urlcollect()
        if not self.files:
            it = iterm.iterm()
            it.terminit()
        if self.items:
            ulist = '\n'.join(self.items)
            uspec = util.plural(len(self.items),
                                ('url', 'message-id')[self.ui.proto=='mid'])
            yorn = '%s\nretrieve the above %s? yes, [No] ' % (ulist, uspec)
            answer = raw_input(yorn).lower()
        else:
            msg = 'no %ss found. [ok] ' % ('url',
                                           'message-id')[self.ui.proto=='mid']
            raw_input(msg)
            answer = ''
        if not self.files:
            it.reinit()
        if answer in ('y', 'yes'):
            self.urlgo()
