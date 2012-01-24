# -*- coding: utf-8 -*-
import os
import urllib2
import hashlib

class HttpFetcher(object):
    cache_dir = None

    def set_cache_dir(self, dir):
        self.cache_dir = dir

    def _create_path_for_file(self, fname):
        dirname = os.path.dirname(fname)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

    def get_fname(self, url, prefix):
        hash = hashlib.sha1(url.replace('/', '-')).hexdigest()
        fname = '%s/%s/%s' % (self.cache_dir, prefix, hash)
        return fname

    def open_url(self, url, prefix, error_ok=False, return_url=False):
        final_url = None
        fname = None
        if self.cache_dir:
            fname = self.get_fname(url, prefix)
        if not fname or not os.access(fname, os.R_OK):
            opener = urllib2.build_opener(urllib2.HTTPHandler)
            opener.addheaders = [('User-agent', 'Mozilla/5.0')]
            try:
                f = opener.open(url)
            except urllib2.URLError:
                if error_ok:
                    return None
                raise
            s = f.read()
            final_url = f.geturl()
            if fname:
                self._create_path_for_file(fname)
                outf = open(fname, 'w')
                outf.write(s)
                outf.close()
        else:
            f = open(fname)
            s = f.read()
        f.close()
        if return_url:
            return s, final_url
        return s
