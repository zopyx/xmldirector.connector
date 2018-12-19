# -*- coding: utf-8 -*-

################################################################
# xmldirector.connector
# (C) 2019,  Andreas Jung, www.zopyx.com, Tuebingen, Germany
################################################################


import os
import json
import inspect
import datetime
import pkg_resources

import plone.api
from zope.component import getUtility
from plone.registry.interfaces import IRegistry
from plone.app.registry.browser import controlpanel
from Products.Five.browser import BrowserView

from xmldirector.connector.i18n import MessageFactory as _
from xmldirector.connector.interfaces import IConnectorSettings
from xmldirector.connector.interfaces import IConnectorHandle


class DBSettingsEditForm(controlpanel.RegistryEditForm):

    schema = IConnectorSettings
    label = _(u'XML Director Connector settings')
    description = _(u'')

    def updateFields(self):
        super(DBSettingsEditForm, self).updateFields()

    def updateWidgets(self):
        super(DBSettingsEditForm, self).updateWidgets()


class DBSettingsControlPanel(controlpanel.ControlPanelFormWrapper):
    form = DBSettingsEditForm

    @property
    def settings(self):
        """ Returns setting as dict """
        registry = getUtility(IRegistry)
        settings = registry.forInterface(IConnectorSettings)
        result = dict()
        for name in settings.__schema__:
            result[name] = getattr(settings, name)
        return result

    def settings_json(self):
        """ Returns setting as JSON """
        return json.dumps(self.settings)
