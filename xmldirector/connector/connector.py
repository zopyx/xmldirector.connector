# -*- coding: utf-8 -*-

################################################################
# xmldirector.connector
# (C) 2019,  Andreas Jung, www.zopyx.com, Tuebingen, Germany
################################################################

import fs
import fs.errors
import furl
import pkg_resources

from zope import schema
from zope.interface import implementer
from zope.component import getUtility
from plone.dexterity.content import Item
from plone.supermodel import model
from plone.registry.interfaces import IRegistry

from xmldirector.connector.i18n import MessageFactory as _
from xmldirector.connector.interfaces import IConnectorSettings
from xmldirector.connector.logger import LOG

# determine all entry points


def supported_protocols():

    protocols = []
    for d in pkg_resources.working_set:
        for protocol in pkg_resources.get_entry_map(d.project_name,
                                                    'fs.opener'):
            protocols.append(protocol)
    return protocols


SUPPORTED_FS_SCHEMAS = supported_protocols()
LOG.warn('Supported fs protocols: {}'.format(SUPPORTED_FS_SCHEMAS))


class IConnector(model.Schema):

    connector_url = schema.TextLine(
        title=_(u'(optional) connection URL of storage'),
        description=_(
            u'WebDAV: http://host:port/path/to/webdav, '
            'Local filesystem: file://path/to/directory, '
            'AWS S3: s3://bucketname, ', 'SFTP sftp://host/path, '
            'FTP: ftp://host/path'),
        required=False)

    connector_username = schema.TextLine(
        title=_(u'(optional) username overriding the system settings'),
        required=False)

    connector_password = schema.Password(
        title=_(u'(optional) password overriding the system settings'),
        required=False)

    connector_subpath = schema.TextLine(
        title=_(u'Subdirectory relative to the global connection URL'),
        description=_(
            u'Use this value for configuring a more specific subpath'),
        required=False)

    connector_readonly = schema.Bool(
        title=_(u'Readonly access'), default=False, required=False)


@implementer(IConnector)
class Connector(Item):
    def get_connector_url(self, subpath=None, hide_password=False):

        url = ''
        username = ''
        password = ''

        # check local connector URL first
        if self.connector_url:
            url = self.connector_url
            username = self.connector_username
            password = self.connector_password
        else:
            # global URL settings
            registry = getUtility(IRegistry)
            settings = registry.forInterface(IConnectorSettings)
            url = settings.connector_url
            username = settings.connector_username
            password = settings.connector_password

        username = username or ''
        password = password or ''
        if not url:
            raise ValueError(
                'No connector URL configured (neither local nor global)')

        f = furl.furl(url)
        if username:
            f.username = username
        if password:
            f.password = 'secret' if hide_password else password
        if self.connector_subpath:
            f.path.add(self.connector_subpath)
        if subpath:
            f.path.add(subpath)

        if f.scheme not in SUPPORTED_FS_SCHEMAS:
            LOG.warn('Unsupported scheme: {}'.format(f.scheme))
        return f.tostr()

    def get_handle(self, subpath=None):
        url = self.get_connector_url(subpath)
        return fs.open_fs(url)
