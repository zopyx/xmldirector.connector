# -*- coding: utf-8 -*-

################################################################
# xmldirector.plonecore
# (C) 2016,  Andreas Jung, www.zopyx.com, Tuebingen, Germany
################################################################

import os
import uuid
import unittest
import six

import plone.api
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import applyProfile
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import IntegrationTesting
from plone.app.testing import setRoles
from plone.app.testing import login
from plone.testing import zope
from plone.registry.interfaces import IRegistry

from zope.component import getUtility
from zope.configuration import xmlconfig
from AccessControl.SecurityManagement import newSecurityManager

from xmldirector.connector.interfaces import IConnectorSettings
from xmldirector.connector.logger import LOG

import xmldirector.connector
import plone.app.dexterity

CONNECTOR_URL = os.environ.get('CONNECTOR_URL', 'file:///tmp')
CONNECTOR_USERNAME = os.environ.get('CONNECTOR_USERNAME', 'admin')
CONNECTOR_PASSWORD = os.environ.get('CONNECTOR_PASSWORD', 'admin')

os.environ['TESTING'] = '1'


class PolicyFixture(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE, )

    def setUpZope(self, app, configurationContext):
        for mod in [
                plone.app.dexterity,
                xmldirector.connector,
        ]:
            xmlconfig.file('configure.zcml', mod, context=configurationContext)

    def setUpPloneSite(self, portal):
        # Install into Plone site using portal_setup
        applyProfile(portal, 'xmldirector.connector:default')
        portal.acl_users.userFolderAddUser('god', 'dummy', ['Manager'], [])
        portal.acl_users.userFolderAddUser('god2', 'dummy', ['Manager'], [])
        setRoles(portal, 'god', ['Manager'])
        setRoles(portal, 'god2', ['Manager'])
        login(portal, 'god')

        self.testing_directory = u'testing-{}'.format(uuid.uuid4())

        self.connector = plone.api.content.create(type='xmldirector.connector', container=plone.api.portal.get(), id='connector')

        registry = getUtility(IRegistry)
        settings = registry.forInterface(IConnectorSettings)
        settings.connector_username = six.text_type(CONNECTOR_USERNAME)
        settings.connector_password = six.text_type(CONNECTOR_PASSWORD)
        settings.connector_url = six.text_type(CONNECTOR_URL)

        handle = self.connector.get_handle()
        handle.makedir(self.testing_directory)

        settings.connector_url = CONNECTOR_URL + '/' + self.testing_directory

        if not handle.exists(self.testing_directory):
            handle.makedir(self.testing_directory)

    def tearDownPloneSite(self, app):

        registry = getUtility(IRegistry)
        settings = registry.forInterface(IConnectorSettings)
        settings.connector_url = six.text_type(CONNECTOR_URL)

        handle = self.connector.get_handle()

        try:
            handle.removedir(self.testing_directory)
        except Exception as e:
            LOG.error('tearDownZope() failed ({})'.format(e))
        zope.uninstallProduct(app, 'xmldirector.connector')

POLICY_FIXTURE = PolicyFixture()
POLICY_INTEGRATION_TESTING = IntegrationTesting(bases=(POLICY_FIXTURE, ), name='PolicyFixture:Integration')


class TestBase(unittest.TestCase):

    layer = POLICY_INTEGRATION_TESTING

    @property
    def portal(self):
        return self.layer['portal']

    def login(self, uid='god'):
        """ Login as manager """
        user = self.portal.acl_users.getUser(uid)
        newSecurityManager(None, user.__of__(self.portal.acl_users))
