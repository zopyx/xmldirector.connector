# -*- coding: utf-8 -*-

################################################################
# xmldirector.connector
# (C) 2019,  Andreas Jung, www.zopyx.com, Tuebingen, Germany
################################################################

import sys

from xmldirector.connector.logger import LOG

if sys.version_info.major < 3:
    raise RuntimeError('xmldirector.connector requires Python 3 or higher. No support for Python 2. Python 2 is dead')

# Check filesystem encoding
fs_enc = sys.getfilesystemencoding()
if fs_enc.lower() not in ('utf8', 'utf-8'):
    LOG.error('Filesystem encoding should be UTF-8, not {}'.format(fs_enc))
