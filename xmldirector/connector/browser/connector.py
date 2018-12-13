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
        return '/'.join(self._subpath) or '.'

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
class HighlightConnector(RawConnector):

    template = ViewPageTemplateFile('connector_highlight.pt')

    @property
    def mimetype(self):
        """ Mimetype of references file """
        return mimetypes.guess_type(self.subpath)[0]

    @property
    def content(self):
        """ Return references content """
        handle = self.context.get_handle()
        with handle.open(self.subpath) as fp:
            return fp.read()

    def __call__(self, *args, **kw):
        return self.template()


@implementer(IPublishTraverse)
class Connector(RawConnector):

    template = ViewPageTemplateFile('connector_view.pt')

    def breadcrumbs(self):
        """ Breadcrumbs """

        current_url = self.context.absolute_url()
        result = list()
        for i in range(len(self._subpath)):
            sp = '/'.join(self._subpath[:i+1])
            href = f'{current_url}/view/{sp}'
            result.append(dict(href=href, title=self._subpath[i]))

        return result

    def get_entries(self):
        handle = self.context.get_handle()
        result =  list(handle.filterdir(self.subpath,namespaces=['basic', 'access', 'details']))
        result = sorted(result, key=operator.attrgetter('name'))
        return result

    def folder_contents(self, subpath='.'):
        """" REST endpoint  """

        handle = self.context.get_handle()
        entries = list(handle.filterdir(subpath,namespaces=['basic', 'access', 'details']))
        result = []
        context_url = self.context.absolute_url()
        for row in sorted(entries, key=operator.attrgetter('name')):

            user = group = ''
            if 'access' in row.namespaces:
                user = row.user
                group = row.group

            size = modified = ''
            if 'details' in row.namespaces:
                size = row.size
                modified = row.modified.timestamp()

            result.append(dict(
                name=row.name,
                is_file=row.is_file,
                is_dir=row.is_dir,
                size=size,
                user=user,
                group=group,
                modified=modified,
                view_url = f'{context_url}/view/{subpath}/{row.name}',
                raw_url = f'{context_url}/raw/{subpath}/{row.name}',
                highlight_url = f'{context_url}/highlight/{subpath}/{row.name}',
            ))

        self.request.response.setHeader('content-type', 'application/json')
        print(result)
        return json.dumps(result)

    def __call__(self, *args, **kw):
        return self.template()
