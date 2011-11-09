#!/usr/bin/python

import os, subprocess

print "Running pip..."
subprocess.call("pip install -r requirements.txt", shell=True)

import settings

IMAGE_PATHS = ('images/members', 'images/orgs', 'images/parties',
               'images/users', 'gen')

all_paths = IMAGE_PATHS
all_paths += (settings.MEDIA_TMP_DIR, )

for path in all_paths:
    full_path = '%s%s' % (settings.MEDIA_ROOT, path)
    try:
        os.mkdir(full_path)
    except OSError:
        pass

if not hasattr(settings, 'LESS_PATH') or not os.access(settings.LESS_PATH, os.X_OK):
    print "LESS_PATH is not set correctly in settings_local.py."
    print "Make sure it points to a working lessc binary."
