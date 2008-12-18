# $Id$

import urlregex, util
import os.path, urllib2

class wget(object):
    def __init__(self, ui, headers=None):
        self.ui = ui
        self.opener = urllib2.build_opener()
        if headers:
            self.opener.addheaders = headers

    def wwarn(self, url, inst):
        if hasattr(inst, 'reason'):
            self.ui.warn('failed to reach a server for %s\n' % url,
                         'reason: %s\n' % inst)
        else:
            self.ui.warn('server failure for %s\n' % url,
                         'error code: %s\n' % inst)

    def request(self, req, func='r'):
        result = None
        try:
            fp = self.opener.open(req)
            if func == 'r':
                result = fp.read()
            elif func == 'g':
                result = fp.geturl()
            elif func == 'i':
                result = fp.info()
            else:
                raise util.DeadMan('%s: invalid request instruction')
            fp.close()
        except urllib2.URLError, inst:
            if hasattr(inst, 'reason'):
                self.ui.warn('failed to reach a server for %s\n' % req,
                             'reason: %s\n' % inst)
            else:
                self.ui.warn('server failure for %s\n' % req,
                             'error code: %s\n' % inst)
        return result

    def download(self, urls):
        self.ui.getdir = util.savedir(self.ui.getdir)
        for url in map(urlregex.webschemecomplete, urls):
            s = self.request(url)
            if s:
                try:
                        bn = url.rstrip('/').split('/')[-1]
                        path = os.path.join(self.ui.getdir, bn)
                        self.ui.note('downloading to %s ...\n' % path)
                        fp = open(path, 'wb')
                        fp.write(s)
                        fp.close()
                except IOError, inst:
                    raise util.DeadMan(inst)
