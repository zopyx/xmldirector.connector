# -*- coding: utf-8 -*-

################################################################
# xmldirector.connector
# (C) 2019,  Andreas Jung, www.zopyx.com, Tuebingen, Germany
################################################################

import operator
import fs
import fs.errors
import furl
from fs.opener import registry as fs_opener_registry
import plone.api
from plone.dexterity.content import Item
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from plone.registry.interfaces import IRegistry
from plone.autoform import directives as form
from zope.schema.interfaces import IContextSourceBinder
import zope.interface
from z3c.form.browser.select import SelectWidget
from plone.supermodel import model
from xmldirector.connector.i18n import MessageFactory as _
from xmldirector.connector.interfaces import IConnectorSettings
from xmldirector.connector.logger import LOG
from zope import schema
from zope.component import getUtility
from zope.interface import implementer

# determine all entry points
SUPPORTED_FS_SCHEMAS = fs_opener_registry.protocols
LOG.info('Supported fs protocols: {}'.format(SUPPORTED_FS_SCHEMAS))


def get_connector_references(context):
    """ Read guideline topics from portal annotation """

    catalog = plone.api.portal.get_tool('portal_catalog')
    query = dict(portal_type='xmldirector.connector')
    items = list()
    for brain in catalog(**query):
        items.append(SimpleTerm(brain.UID, brain.UID, brain.Title))
    items.sort(key=operator.attrgetter("title"))
    return SimpleVocabulary(items)


zope.interface.directlyProvides(get_connector_references, IContextSourceBinder)


class IConnector(model.Schema):

    connector_url = schema.TextLine(title=_(u'(optional) connection URL of storage'),
                                    description=_(
                                        u'WebDAV: webdav://host:port/path/to/webdav, '
                                        'local filesystem: file://path/to/directory, '
                                        'AWS S3: s3://bucketname, ', 'SFTP sftp://host/path'),
                                    required=False)

    connector_username = schema.TextLine(title=_(u'(optional) username overriding the system settings'), required=False)

    connector_password = schema.Password(title=_(u'(optional) password overriding the system settings'), required=False)

    connector_subpath = schema.TextLine(title=_(u'Subdirectory relative to the global connection URL'),
                                        description=_(u'Use this value for configuring a more specific subpath'),
                                        required=False)

    connector_readonly = schema.Bool(title=_(u'Readonly access'), default=False, required=False)

    form.widget("connector_reference", SelectWidget)
    connector_reference = schema.Choice(
        title=_("Reference to other connector "),
        required=False,
        source=get_connector_references,
        default=None,
    )


@implementer(IConnector)
class Connector(Item):
    def get_connector_url(self, subpath=None, hide_password=False):

        # check local connector URL first
        connector_url = getattr(self, 'connector_url', None)
        if connector_url:
            url = connector_url
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
            raise ValueError('No connector URL configured (neither local nor global)')

        f = furl.furl(url)
        if username:
            f.username = username
        if password:
            f.password = 'secret' if hide_password else password
        if self.connector_subpath:
            f.path.add(self.connector_subpath)
        if subpath:
            f.path.add(subpath)

        if f.scheme and f.scheme not in SUPPORTED_FS_SCHEMAS:
            LOG.warning('Unsupported scheme: {} in {}'.format(f.scheme, f.tostr()))
        return f.tostr()

    def get_handle(self, subpath=None):
        def escaped_url(url):
            """ Remove credentials from url """
            f = furl.furl(url)
            f.username = None
            f.password = None
            return f.tostr()

        # a connector may reference another connector as "parent"
        if self.connector_reference:
            uid = self.connector_reference
            catalog = plone.api.portal.get_tool("portal_catalog")
            brains = catalog(UID=uid)
            if brains:
                connector_reference = brains[0].getObject()
                url = connector_reference.get_connector_url(subpath)
            else:
                raise ValueError(
                    f"Referenced connector instance with UID {self.connector_reference} not found. Please remove reference from field 'connector_reference'."
                )
        else:
            # default: either use locally configured connector URL or fallback to global connector configuration
            url = self.get_connector_url(subpath)

        try:
            return fs.open_fs(url)
        except fs.errors.CreateFailed as e:
            url2 = escaped_url(url)
            raise IOError('Unable to open fs {0} ({1}'.format(url2, e))
