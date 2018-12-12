# -*- coding: utf-8 -*-

################################################################
# xmldirector.plonecore
# (C) 2016,  Andreas Jung, www.zopyx.com, Tuebingen, Germany
################################################################

import os
import fs
import stat
import json
import datetime
import fs.errors
import itertools
import fs.path
import humanize
import operator
import hurry.filesize
import tempfile
import mimetypes
import unicodedata
import logging
import pkg_resources

import zExceptions
from zope.interface import implementer
from zope.interface import alsoProvides
from zope.publisher.interfaces import IPublishTraverse
from plone.app.layout.globals.interfaces import IViewView
from plone.protect.interfaces import IDisableCSRFProtection
from AccessControl.SecurityManagement import getSecurityManager
from ZPublisher.Iterators import IStreamIterator
from Products.CMFCore import permissions
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from xmldirector.connector.i18n import MessageFactory as _

import io


LOG = logging.getLogger('xmldirector.connector')


@implementer(IPublishTraverse)
class RawConnector(BrowserView):

    def __init__(self, context, request):
        super(RawConnector, self).__init__(context, request)
        self._subpath = []

    def publishTraverse(self, request, name):
        if not hasattr(self, '_subpath'):
            self._subpath = []
        self._subpath.append(name)
        return self

    @property
    def subpath(self):
        return '/'.join(self._subpath)

    def __call__(self):
        """ Download given file """
        handle = self.context.get_handle()
        filename = self.subpath
        if not handle.exists(filename):
            raise zExceptions.NotFound(f'{filename} does not exist')
        basename = os.path.basename(filename)
        basename, ext = os.path.splitext(basename)
        mt, encoding = mimetypes.guess_type(filename)
        self.request.response.setHeader('content-type', mt)
        self.request.response.setHeader(
            'content-length', handle.getsize(filename))
        if 'download' in self.request.form:
            self.request.response.setHeader(
                'content-disposition', 'attachment; filename={}'.format(os.path.basename(filename)))
        # iterator?
        with handle.open(filename, 'rb') as fp:
            self.request.response.write(fp.read())


@implementer(IPublishTraverse)
class Connector(RawConnector):

    def get_entries(self):
        handle = self.context.get_handle()
        result =  handle.filterdir(self.subpath)
        return result
