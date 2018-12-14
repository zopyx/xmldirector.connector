# -*- coding: utf-8 -*-

################################################################
# xmldirector.plonecore
# (C) 2016,  Andreas Jung, www.zopyx.com, Tuebingen, Germany
################################################################

import io
import os
import fs
import fs.zipfs
import six
import json
import datetime
import tempfile
import fs.errors
import fs.path
import operator
import mimetypes
import unicodedata
import logging

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

    def __call__(self, *args, **kw):
        return self.template()

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

            mimetype, _ = mimetypes.guess_type(row.name)

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
                mimetype=mimetype,
                user=user,
                group=group,
                modified=modified,
                view_url = f'{context_url}/view/{subpath}/{row.name}',
                raw_url = f'{context_url}/raw/{subpath}/{row.name}',
                highlight_url = f'{context_url}/highlight/{subpath}/{row.name}',
            ))

        self.request.response.setHeader('content-type', 'application/json')
        return json.dumps(result)

    def upload_file(self):
        """ AJAX callback for Uploadify """

        get_handle = self.context.get_handle()
        filename = os.path.basename(self.request.file.filename)
        basename, ext = os.path.splitext(filename)

        with get_handle.open(fs.path.join(self.subpath, filename), 'wb') as fp:
            self.request.file.seek(0)
            data = self.request.file.read()
            fp.write(data)

        self.request.response.setStatus(200)

    def zip_import_ui(self, zip_file=None, subpath=None, clean_directories=None):
        """ Import WebDAV subfolder from an uploaded ZIP file """

        try:
            imported_files = self.zip_import(
                zip_file, subpath, clean_directories)
        except Exception as e:
            msg = u'ZIP import failed'
            LOG.error(msg, exc_info=True)
            return self.redirect(msg, 'error')

        self.logger.log(
            'ZIP file imported ({}, {} files)'.format(zip_file, len(imported_files)), details=imported_files)
        return self.redirect(_(u'Uploaded ZIP archive imported'), subpath=subpath)

    def zip_import(self, zip_file=None):
        """ Import subfolder from an uploaded ZIP file """

        subpath = self.request.get('subpath') or self.subpath
        handle = self.context.get_handle(subpath)

        if not zip_file:
            zip_filename = self.request.zipfile.filename
            temp_fn = tempfile.mktemp(suffix='.zip')
            with open(temp_fn, 'wb') as fp:
                self.request.zipfile.seek(0)
                fp.write(self.request.zipfile.read())
            zip_file = temp_fn
        else:
            zip_filename = zip_file

        if not zip_filename:
            raise ValueError(
                u'No filename detected. Did you really upload a ZIP file?')
        if not zip_filename.endswith('.zip'):
            raise ValueError(
                u'Upload file did not end with .zip. Did you really upload a ZIP file?')

        try:
            with fs.zipfs.ZipFS(zip_file, encoding='utf-8') as zip_handle:

                # import all files from ZIP into WebDAV
                count = 0
                dirs_created = set()
                for i, name in enumerate(zip_handle.walk.files()):

                    target_filename = unicodedata.normalize(
                        'NFC', name).lstrip('/')
                    if self.subpath:
                        target_filename = u'{}/{}'.format(
                            self.subpath, target_filename)

                    target_dirname = '/'.join(target_filename.split('/')[:-1])
                    if target_dirname not in dirs_created:
                        try:
                            handle.makedir(
                                target_dirname, recreate=True)
                            dirs_created.add(target_dirname)
                        except Exception as e:
                            LOG.error(
                                'Failed creating {} failed ({})'.format(target_dirname, e))

                    LOG.info(u'ZIP filename({})'.format(name))

                    out_fp = handle.open(target_filename, 'wb')
                    zip_fp = zip_handle.open(name, 'rb')
                    out_fp.write(zip_fp.read())
                    out_fp.close()
                    count += 1

        except Exception as e:
            msg = 'Error opening ZIP file: {}'.format(e)
            raise

        self.request.response.redirect(self.context.absolute_url() + '/' + self.subpath)
