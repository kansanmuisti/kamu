# -*- coding: utf-8 -*-
import os
import urllib.request, urllib.error, urllib.parse
import hashlib

cache_dir = None

def set_cache_dir(dir):
    global cache_dir
    cache_dir = dir

def create_path_for_file(fname):
    dirname = os.path.dirname(fname)
    if not os.path.exists(dirname):
        os.makedirs(dirname)

def get_fname(url, prefix):
    hash = hashlib.sha1(url.replace('/', '-')).hexdigest()
    fname = '%s/%s/%s' % (cache_dir, prefix, hash)
    return fname

def open_url(url, prefix, skip_cache=False, error_ok=False, return_url=False):
    final_url = None
    fname = None
    if cache_dir and not skip_cache:
        fname = get_fname(url, prefix)
    if not fname or not os.access(fname, os.R_OK):
        opener = urllib.request.build_opener(urllib.request.HTTPHandler)
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        try:
            f = opener.open(url)
        except urllib.error.URLError:
            if error_ok:
                return None
            raise
        s = f.read()
        final_url = f.geturl()
        if fname:
            create_path_for_file(fname)
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
