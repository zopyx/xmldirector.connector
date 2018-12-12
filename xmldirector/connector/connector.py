# -*- coding: utf-8 -*-

################################################################
# xmldirector.connector
# (C) 2019,  Andreas Jung, www.zopyx.com, Tuebingen, Germany
################################################################


import fs
import fs.errors
import furl

import zExceptions
from zope import schema
from zope.interface import implementer
from zope.component import getUtility
from plone.dexterity.content import Item
from plone.supermodel import model
from plone.registry.interfaces import IRegistry

from xmldirector.connector.i18n import MessageFactory as _
from xmldirector.connector.interfaces import IConnectorSettings
from xmldirector.connector.interfaces import IConnectorHandle
from xmldirector.connector.logger import LOG


class IConnector(model.Schema):

    connector_url = schema.TextLine(
        title=_(u'(optional) connection URL of storage'),
        description=_(u'WebDAV: http://host:port/path/to/webdav, '
                      'Local filesystem: file://path/to/directory, '
                      'AWS S3: s3://bucketname, ',
                      'SFTP sftp://host/path, '
                      'FTP: ftp://host/path'),
        required=False
    )

    connector_username = schema.TextLine(
        title=_(u'(optional) username overriding the system settings'),
        required=False
    )

    connector_password = schema.Password(
        title=_(u'(optional) password overriding the system settings'),
        required=False
    )

    connector_subpath = schema.TextLine(
        title=_(u'Subdirectory relative to the global connection URL'),
        description=_(
            u'Use this value for configuring a more specific subpath'),
        required=False
    )

    default_view_anonymous = schema.TextLine(
        title=_(u'Default view (anonymous)'),
        description=_(
            u'Name of a default view for site visitors without edit permission'),
        required=False,
        default=None,
    )

    default_view_authenticated = schema.TextLine(
        title=_(u'Default view (authenticated)'),
        description=_(u'Name of a default view for anonymous site visitors'),
        required=False,
        default=u'@@view',
    )


@implementer(IConnector)
class Connector(Item):

    def get_handle(self):
        f = furl.furl(self.connector_url)
        if self.connector_username:
            f.username = self.connector_username
        if self.connector_password:
            f.password = self.connector_password
        return fs.open_fs(f.tostr())
