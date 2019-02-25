# -*- coding: utf-8 <script type="text/javascript" src="js/olark.js"></script>

################################################################
# xmldirector.plonecore
# (C) 2016,  Andreas Jung, www.zopyx.com, Tuebingen, Germany
################################################################

import os
import sys
import uuid
import datetime
from zipfile import ZipFile
from .base import TestBase
from .base import CONNECTOR_URL
import zExceptions

PREFIX = 'testing-{}'.format(uuid.uuid4())

is_mac = sys.platform == 'darwin'
is_mac = False


class BasicTests(TestBase):

    def _get_view(self):
        from xmldirector.connector.browser.connector import Connector
        return Connector(self.portal.connector, self.portal.connector.REQUEST)

    def testCheckPortalType(self):
        assert self.portal.connector.portal_type == 'xmldirector.connector'

    def testFileCheck(self):
        handle = self.portal.connector.get_handle()
        self.assertEqual(handle.exists(u'foo/index.html'), False)
        self.assertEqual(handle.exists(u'foo/index.xml'), False)
        self.assertEqual(handle.exists(u'foo/xxxx.html'), False)

    def testRenameCollection(self):
        self.login('god')
        view = self._get_view()
        view.new_folder(u'foo')
        view.rename(u'foo', u'bar')
        handle = self.portal.connector.get_handle()
        self.assertEqual(handle.exists(u'foo'), False)
        self.assertEqual(handle.exists(u'bar'), True)

    def testCreateCollection(self):
        self.login('god')
        view = self._get_view()
        view.new_folder(u'new')
        handle = self.portal.connector.get_handle()
        self.assertEqual(handle.exists(u'new'), True)

    def testRemoveCollection(self):
        self.login('god')
        view = self._get_view()
        view.new_folder(u'foo')
        view.remove(u'foo')
        handle = self.portal.connector.get_handle()
        self.assertEqual(handle.exists(u'foo'), False)

    def testRenderControlPanel(self):
        with self.assertRaises(zExceptions.Unauthorized):
            view = self.portal.restrictedTraverse('@@connector-settings')
            view()

        self.login('god')
        view = self.portal.restrictedTraverse('@@connector-settings')
        view()

    def testTraversalNonExistingPath(self):
        path = 'connector/@@view/foo/doesnotexist.html'
        with self.assertRaises(zExceptions.NotFound):
            self.portal.restrictedTraverse(path)

        obj = self.portal.restrictedTraverse(path, None)
        assert obj == None

    def testTraversalExistingPath(self):
        handle = self.portal.connector.get_handle()
        handle.makedir(u'foo')
        with handle.open(u'foo/foo.bar', 'w') as fp:
            fp.write(u'1234567')
        path = 'connector/@@view/foo/foo.bar'
        result = self.portal.restrictedTraverse(path)
        assert result.wrapped_info.size == 7

    def testZipImport(self):
        self.login('god')
        fn = os.path.join(os.path.dirname(__file__), 'zip_data', 'sample.zip')
        view = self._get_view()
        view.zip_import(fn)
        handle = self.portal.connector.get_handle()
        self.assertEqual(handle.exists(u'import/test.xml'), True)
        self.assertEqual(handle.exists(u'import/test.html'), True)

    def _testZipImportMacZip(self):
        self.login('god')
        handle = self.portal.connector.get_handle()
        for name in handle.listdir('.'):
            handle.removedir(name)

        fn = os.path.join(os.path.dirname(__file__), 'zip_data', 'created_macosx_zip.zip')
        view = self._get_view()
        view.zip_import(fn)
        names = handle.listdir()
        if is_mac:
            self.assertEquals(u'üüüü' in names, True, names)


class BasicTests2(TestBase):
    def testZipExport(self):
        self.login('god')
        view = self._get_view()
        fn = view.filemanager_zip_download(subpath='', download=False)
        zf = ZipFile(fn, 'r')
        self.assertEqual('foo/index.html' in zf.namelist(), True)
        self.assertEqual('foo/index.xml' in zf.namelist(), True)
        if is_mac:
            self.assertEqual('üöä/üöä.xml' in zf.namelist(), True)
        zf.close()
        os.unlink(fn)

    def testZipExportFoo2Only(self):
        self.login('god')
        view = self._get_view()
        fn = view.filemanager_zip_download(subpath='foo2', download=False)
        zf = ZipFile(fn, 'r')
        self.assertEqual('foo/index.html' not in zf.namelist(), True)
        self.assertEqual('foo/index.xml' not in zf.namelist(), True)
        self.assertEqual('foo2/index.html' in zf.namelist(), True)
        self.assertEqual('foo2/index.xml' in zf.namelist(), True)
        zf.close()
        os.unlink(fn)

    def testZipExportReimport(self):
        handle = self.portal.connector.get_handle()
        self.login('god')

        view = self._get_view()
        fn = view.filemanager_zip_download(subpath='', download=False)

        for name in handle.listdir():
            handle.removedir(name, False, True)

        view.zip_import(fn)
        dirs = handle.listdir()
        self.assertEqual('foo' in dirs, True)
        self.assertEqual('foo2' in dirs, True)
        if is_mac:
            self.assertEqual(u'üöä' in dirs, True)

    def testZipExport(self):
        self.login('god')
        view = self._get_view()
        fn = view.filemanager_zip_download(subpath='', download=False)
        zf = ZipFile(fn, 'r')
        self.assertEqual('foo/index.html' in zf.namelist(), True)
        self.assertEqual('foo/index.xml' in zf.namelist(), True)
        if is_mac:
            self.assertEqual('üöä/üöä.xml' in zf.namelist(), True)
        zf.close()
        os.unlink(fn)

    def __testZipImportMacFinder(self):
        self.login('god')
        handle = self.portal.connector.get_handle()
        for name in handle.listdir():
            handle.removedir(name, False, True)

        fn = os.path.join(os.path.dirname(__file__), 'zip_data', 'created_macosx_finder.zip')
        view = self._get_view()
        view.zip_import(fn)
        names = handle.listdir()
        if is_mac:
            self.assertEquals(u'üüüü' in names, True, names)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(BasicTests))
    return suite
