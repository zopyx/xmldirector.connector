# -*- coding: utf-8 -*-

################################################################
# xmldirector.connector
# (C) 2019,  Andreas Jung, www.zopyx.com, Tuebingen, Germany
################################################################

import os
import fs
import fs.zipfs
import json
import furl
import tempfile
import fs.errors
import fs.path
import fs.copy
import fs.zipfs
import mimetypes
import unicodedata
import logging

import zExceptions
import plone.api
from zope.component import queryUtility
from zope.interface import implementer
from zope.publisher.interfaces import IPublishTraverse
from ZPublisher.Iterators import IStreamIterator
from Products.statusmessages.interfaces import IStatusMessage
from Products.CMFCore import permissions
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from xmldirector.connector.i18n import MessageFactory as _
from xmldirector.connector.interfaces import IViewDispatcher

TEXT_MIMETYPES = set(['application/json', 'application/javascript'])

LOG = logging.getLogger('xmldirector.connector')


def safe_unicode(s):
    if not isinstance(s, str):
        return s.decode("utf8")
    return s


@implementer(IStreamIterator)
class connector_iterator():
    """ Iterator for pyfilesystem content """
    def __init__(self, handle, filename, mode='rb', streamsize=1 << 24):
        self.handle = handle
        self.fp = handle.open(filename, mode)
        self.filename = filename
        self.streamsize = streamsize

    def __iter__(self):
        return self

    def __next__(self):
        data = self.fp.read(self.streamsize)
        if not data:
            self.fp.close()
            raise StopIteration
        return data

    next = __next__

    def seek(self, *args):
        pass

    def __len__(self):
        return self.handle.getsize(self.filename)

    def read(self, size):
        data = self.fp.read(size)
        if not data:
            self.fp.close()
            raise StopIteration
        return data


@implementer(IPublishTraverse)
class RawConnector(BrowserView):
    def __init__(self, context, request):
        super(RawConnector, self).__init__(context, request)
        self._subpath = []
        self.traversal_subpath = []

    def publishTraverse(self, request, name):
        if not hasattr(self, '_subpath'):
            self._subpath = []
        self._subpath.append(name)
        return self

    @property
    def connector_url(self):
        return self.context.get_connector_url(self.subpath, hide_password=True)

    @property
    def is_readonly(self):
        return self.context.connector_readonly

    @property
    def can_edit(self):
        return not self.is_readonly and plone.api.user.has_permission(permissions.ModifyPortalContent, obj=self.context)

    @property
    def messages(self):
        return IStatusMessage(self.request)

    @property
    def subpath(self):
        return '/'.join(self._subpath)

    def __call__(self):
        """ Download given file """
        handle = self.context.get_handle()
        filename = self.subpath
        if not handle.exists(filename):
            raise zExceptions.NotFound('{} does not exist'.format(filename))
        basename = os.path.basename(filename)
        basename, ext = os.path.splitext(basename)
        mt, encoding = mimetypes.guess_type(filename)
        self.request.response.setHeader('content-type', mt)
        if 'download' in self.request.form or 'filename' in self.request.form:
            fn = self.request.get('filename', os.path.basename(filename))
            self.request.response.setHeader('content-disposition', 'attachment; filename="{}"'.format(fn))
        content_length = handle.getsize(filename)
        if content_length:
            self.request.response.setHeader('content-length', str(content_length))
            return connector_iterator(handle, filename)
        else:
            with handle.open(filename, 'rb') as fp:
                data = fp.read()
                self.request.response.setHeader('content-length', str(len(data)))
                return data

    def get_handle(self, subpath=None, root=False):
        """ Returns a webdav handle for the current subpath """

        if not root:
            if not subpath:
                subpath = '/'.join(self.subpath)

        try:
            return self.context.get_handle(subpath)
        except fs.errors.ResourceNotFoundError as e:
            msg = 'eXist-db path {} does not exist'.format(e.url)
            self.context.plone_utils.addPortalMessage(msg, 'error')
            LOG.debug(msg)
            raise zExceptions.NotFound()
        except fs.errors.PermissionDeniedError as e:
            msg = 'eXist-db path {} unauthorized access (check credentials)'.format(e.url)
            self.context.plone_utils.addPortalMessage(msg, 'error')
            LOG.error(msg)
            raise zExceptions.Unauthorized()

    def __bobo_traverse__(self, request, entryname):
        """ Traversal hook for (un)restrictedTraverse() """
        self.traversal_subpath.append(entryname)
        traversal_subpath = '/'.join(self.traversal_subpath)
        handle = self.get_handle()
        if handle.exists(traversal_subpath):
            if handle.isdir(traversal_subpath):
                return self
            elif handle.isfile(traversal_subpath):
                with handle.open(traversal_subpath, 'rb') as fp:
                    data = fp.read()
                self.wrapped_object = data
                self.wrapped_info = handle.getinfo(traversal_subpath, namespaces=['access', 'details'])
                try:
                    self.wrapped_meta = handle.getmeta(traversal_subpath)
                except fs.errors.NoMetaError:
                    self.wrapped_meta = None
                return self
        raise zExceptions.NotFound('not found: {}'.format(entryname))


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
class InlineConnector(HighlightConnector):

    template = ViewPageTemplateFile('connector_inline.pt')


@implementer(IPublishTraverse)
class Connector(RawConnector):

    template = ViewPageTemplateFile('connector_view.pt')

    def __call__(self, *args, **kw):

        if '@@connector-view' in self.request.URL:
            return self.template()

        dispatcher = queryUtility(IViewDispatcher)
        if dispatcher:
            url = None
            try:
                url = dispatcher(self.context).get_url()
            except Exception as e:
                LOG.warn('Calling view dispatcher failed', exc_info=True)
            if url:
                return self.request.response.redirect(url)
        return self.template()

    def _is_text(self, mimetype):
        """ check if particular mimetype is text-ish """
        if not mimetype:
            return False
        if mimetype.startswith('text/'):
            return True
        if mimetype in TEXT_MIMETYPES:
            return True
        return False

    def breadcrumbs(self):
        """ Breadcrumbs """

        current_url = self.context.absolute_url()
        result = list()
        for i in range(len(self._subpath)):
            sp = '/'.join(self._subpath[:i + 1])
            href = '{}/view/{}'.format(current_url, sp)
            result.append(dict(href=href, title=self._subpath[i]))

        return result

    def folder_contents(self, subpath='.'):
        """" REST endpoint  """
        def sort_key(item):
            key = 'A-' if item.is_dir else 'B-'
            return key + item.name

        connector_url = self.context.get_connector_url(subpath)
        f = furl.furl(connector_url)

        context_url = self.context.absolute_url()
        is_readonly = self.is_readonly

        if f.scheme in ['dlna']:

            # work in progress for "poor" drivers that implement only a subset of the
            # full pyfilesystem driver API

            handle = self.context.get_handle(subpath)
            entries = list(handle.listdir(subpath))

            result = []
            for name in sorted(entries):

                mimetype, _ = mimetypes.guess_type(name)
                basename, ext = os.path.splitext(name)

                user = group = ''
                size = modified = ''
                is_text = self._is_text(mimetype)

                result.append(
                    dict(
                        name=name,
                        is_file=True,
                        is_dir=False,
                        size=size,
                        mimetype=mimetype,
                        full_path=fs.path.join(subpath, name),
                        ext=ext,
                        user=user,
                        group=group,
                        modified=modified,
                        can_remove=not is_readonly,
                        view_url='{}/view/{}/{}'.format(context_url, subpath, name),
                        raw_url='{}/raw/{}/{}'.format(context_url, subpath, name),
                        highlight_url='{}/highlight/{}/{}'.format(context_url, subpath, name) if is_text else None,
                    ))

        else:

            handle = self.context.get_handle(subpath)
            entries = list(handle.filterdir('.', namespaces=['basic', 'access', 'details']))
            result = []

            try:
                sorted_entries = sorted(entries, key=sort_key)
            except TypeError:
                LOG.error('Unable to sort entries', exc_info=True)
                # Workaround for mod_dav
                # https://github.com/zopyx/xmldirector.connector/issues/64
                sorted_entries = entries

            for row in sorted_entries:
                mimetype, _ = mimetypes.guess_type(row.name)
                basename, ext = os.path.splitext(row.name)

                user = group = ''
                if 'access' in row.namespaces:
                    user = row.user
                    group = row.group

                size = modified = ''
                if 'details' in row.namespaces:
                    size = row.size
                    try:
                        modified = row.modified.timestamp()
                    except AttributeError:
                        modified = u''

                is_text = self._is_text(mimetype)

                result.append(
                    dict(
                        name=row.name,
                        is_file=row.is_file,
                        is_dir=row.is_dir,
                        size=size,
                        mimetype=mimetype,
                        full_path=fs.path.join(subpath, row.name),
                        ext=ext,
                        user=user,
                        group=group,
                        modified=modified,
                        can_remove=not is_readonly,
                        view_url='{}/view/{}/{}'.format(context_url, subpath, row.name),
                        raw_url='{}/raw/{}/{}'.format(context_url, subpath, row.name),
                        highlight_url='{}/highlight/{}/{}'.format(context_url, subpath, row.name) if is_text else None,
                    ))

        # directory up entry
        if subpath:
            full_path = fs.path.join(*fs.path.parts(subpath)[:-1])
            result.insert(
                0,
                dict(full_path=full_path,
                     name='..',
                     is_file=False,
                     is_dir=True,
                     size=0,
                     mimetype=None,
                     user='',
                     group='',
                     can_remove=False))

        self.request.response.setHeader('content-type', 'application/json')
        return json.dumps(result)

    def upload_file(self):
        """ AJAX callback for Uploadify """

        if self.is_readonly:
            raise zExceptions.Forbidden(_('Connector is readonly'))

        subpath = safe_unicode(self.request.get('subpath', self.subpath))
        filename = safe_unicode(os.path.basename(self.request.file.filename))
        basename, ext = os.path.splitext(filename)

        handle = self.context.get_handle(subpath)

        with handle.open(filename, 'wb') as fp:
            self.request.file.seek(0)
            data = self.request.file.read()
            fp.write(data)

        self.request.response.setStatus(200)

    def rename(self, resource_name, new_name):
        """ Rename a resource """

        if self.is_readonly:
            raise zExceptions.Forbidden(_('Connector is readonly'))

        resource_name = safe_unicode(resource_name)
        new_name = safe_unicode(new_name)

        dirname = fs.path.dirname(resource_name)
        new_resource_name = fs.path.join(dirname, new_name)
        handle = self.context.get_handle()

        if handle.exists(new_resource_name):
            raise ValueError(_('Target {} exists').format(resource_name))

        if handle.isfile(resource_name):
            try:
                handle.move(resource_name, new_resource_name)
            except Exception as e:
                msg = resource_name + _(' could not be moved') + ' ({})'.format(e)
                self.request.response.setStatus(500)
                return msg
        else:
            try:
                fs.move.move_dir(handle, resource_name, handle, new_resource_name)
            except Exception as e:
                msg = resource_name + _(' could not be moved') + ' ({})'.format(e)
                self.request.response.setStatus(500)
                return msg

        msg = _('Renamed {} to {}').format(resource_name, new_name)
        self.request.response.setStatus(200)

    def remove(self, resource_name):
        """ Remove a resource by path/name """

        if self.is_readonly:
            raise zExceptions.Forbidden(_('Connector is readonly'))

        subpath = safe_unicode(self.request.get('subpath', self.subpath))

        handle = self.context.get_handle()
        if not handle.exists(resource_name):
            msg = 'Not found {}'.format(resource_name)
            raise zExceptions.NotFound(msg)

        if handle.isdir(resource_name):
            try:
                handle.removetree(resource_name)
            except Exception as e:
                msg = resource_name + _(' could not be deleted') + ' ({})'.format(e)
                self.request.response.setStatus(500)
                return msg

        elif handle.isfile(resource_name):
            try:
                handle.remove(resource_name)
            except Exception as e:
                msg = _('{} could not be deleted ({})').format(resource_name, e)
                self.request.response.setStatus(500)
                return msg

        else:
            msg = _('Unhandled file type for {}').format(resource_name)
            raise RuntimeError(msg)

        msg = _('Deleted {}').format(resource_name)
        self.request.response.setStatus(200)

    def new_folder(self, name, subpath=None):
        """ Create a new collection ``name`` inside the folder ``subpath `` """

        if self.is_readonly:
            raise zExceptions.Forbidden(_('Connector is readonly'))

        if not name:
            raise ValueError(_('No name given'))

        name = safe_unicode(name)
        subpath = safe_unicode(subpath or self.subpath)
        handle = self.context.get_handle(subpath)

        if handle.exists(name):
            msg = _('{}/{} already exists found').format(subpath, name)
            self.messages.add(msg, 'error')
            return self.request.response.redirect(self.context.absolute_url() + '/view/' + subpath)

        try:
            handle.makedir(name)
        except Exception as e:
            msg = _('{}/{} could not be created ({})').format(subpath, name, str(e))
            self.messages.add(msg, 'error')
            return self.request.response.redirect(self.context.absolute_url() + '/' + subpath)

        msg = _('Created {}/{}').format(subpath, name)
        self.messages.add(msg, 'info')
        self.request.response.redirect(self.context.absolute_url() + '/view/' + subpath + '/' + name)

    def zip_import_ui(self, zip_file=None, subpath=None, clean_directories=None):
        """ Import WebDAV subfolder from an uploaded ZIP file """

        if self.is_readonly:
            raise zExceptions.Forbidden(_('Connector is readonly'))

        try:
            imported_files = self.zip_import(zip_file, subpath, clean_directories)
        except Exception as e:
            msg = u'ZIP import failed'
            LOG.error(msg, exc_info=True)
            return self.redirect(msg, 'error')

        self.logger.log('ZIP file imported ({}, {} files)'.format(zip_file, len(imported_files)),
                        details=imported_files)
        return self.redirect(_(u'Uploaded ZIP archive imported'), subpath=subpath)

    def zip_import(self, zip_file=None):
        """ Import subfolder from an uploaded ZIP file """

        if self.is_readonly:
            raise zExceptions.Forbidden(_('Connector is readonly'))

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
            raise ValueError(u'No filename detected. Did you really upload a ZIP file?')
        if not zip_filename.endswith('.zip'):
            raise ValueError(u'Uploaded file did not end with .zip. Did you really upload a ZIP file?')

        try:
            with fs.zipfs.ZipFS(zip_file, encoding='utf-8') as zip_handle:

                # import all files from ZIP into WebDAV
                count = 0
                dirs_created = set()
                for i, name in enumerate(zip_handle.walk.files()):

                    target_filename = unicodedata.normalize('NFC', name).lstrip('/')
                    if self.subpath:
                        target_filename = u'{}/{}'.format(self.subpath, target_filename)

                    target_dirname = '/'.join(target_filename.split('/')[:-1])
                    if target_dirname not in dirs_created:
                        try:
                            handle.makedirs(target_dirname, recreate=True)
                            dirs_created.add(target_dirname)
                        except Exception as e:

                            LOG.error('Failed creating {} failed ({})'.format(target_dirname, e))

                    LOG.info(u'ZIP filename({})'.format(name))

                    out_fp = handle.open(target_filename, 'wb')
                    zip_fp = zip_handle.open(name, 'rb')
                    out_fp.write(zip_fp.read())
                    out_fp.close()
                    count += 1

        except Exception as e:
            msg = 'Error opening ZIP file: {}'.format(e)
            raise

        self.request.response.redirect(self.context.absolute_url() + '/view/' + subpath)

    def zip_export(self):
        """ export as ZIP """

        handle = self.context.get_handle()
        zip_name = tempfile.mktemp(suffix='.zip')
        with fs.zipfs.ZipFS(zip_name, write=True) as zip_out:
            fs.copy.copy_dir(handle, '/', zip_out, '/')

        self.request.response.setHeader('content-type', 'application/zip')
        self.request.response.setHeader('content-disposition', f'attachment; filename={self.context.getId()}.zip')
        self.request.response.setHeader('content-length', os.path.getsize(zip_name))
        with open(zip_name, 'rb') as fp:
            self.request.response.write(fp.read())
        os.unlink(zip_name)
