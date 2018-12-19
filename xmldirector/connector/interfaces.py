# -*- coding: utf-8 -*-

################################################################
# xmldirector.connector
# (C) 2019,  Andreas Jung, www.zopyx.com, Tuebingen, Germany
################################################################

from zope import schema
from zope.interface import Interface
from xmldirector.connector.i18n import MessageFactory as _


class IBrowserLayer(Interface):
    """A brower layer specific to my product """


class IConnectorHandle(Interface):
    """ Return a DAVFS handle for the system-wide configured conector handle """


class IConnectorSettings(Interface):
    """ Connector settings """

    connector_url = schema.TextLine(
        title=_(u'Connection URL of storage'),
        description=_(u'WebDAV: http://host:port/path/to/webdav,'
                      'Local filesystem: file://path/to/directory, '
                      'AWS S3: s3://bucketname, SFTP sftp://host/path, '
                      'FTP: ftp://host/path'),
        default=u'',
        required=True)

    connector_username = schema.TextLine(
        title=_(u'Username for external storage'),
        description=_(u'Username'),
        default=u'admin',
        required=False)

    connector_password = schema.Password(
        title=_(u'Password external storage'),
        description=_(u'Password'),
        default=u'',
        required=False)
