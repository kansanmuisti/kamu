#!/usr/bin/python

import os

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

