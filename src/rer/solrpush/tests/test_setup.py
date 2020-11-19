# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from rer.solrpush.testing import (
    RER_SOLRPUSH_API_INTEGRATION_TESTING,
)  # noqa: E501
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID

import unittest

try:
    from Products.CMFPlone.utils import get_installer
except ImportError:
    get_installer = None


class TestSetup(unittest.TestCase):
    """Test that rer.solrpush is properly installed."""

    layer = RER_SOLRPUSH_API_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        if get_installer:
            self.installer = get_installer(self.portal, self.layer["request"])
        else:
            self.installer = api.portal.get_tool("portal_quickinstaller")

    def test_product_installed(self):
        """Test if rer.solrpush is installed."""
        self.assertTrue(self.installer.isProductInstalled("rer.solrpush"))

    def test_browserlayer(self):
        """Test that IRerSolrpushLayer is registered."""
        from rer.solrpush.interfaces import IRerSolrpushLayer
        from plone.browserlayer import utils

        self.assertIn(IRerSolrpushLayer, utils.registered_layers())


class TestUninstall(unittest.TestCase):

    layer = RER_SOLRPUSH_API_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        if get_installer:
            self.installer = get_installer(self.portal, self.layer["request"])
        else:
            self.installer = api.portal.get_tool("portal_quickinstaller")
        roles_before = api.user.get_roles(TEST_USER_ID)
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.installer.uninstallProducts(["rer.solrpush"])
        setRoles(self.portal, TEST_USER_ID, roles_before)

    def test_product_uninstalled(self):
        """Test if rer.solrpush is cleanly uninstalled."""
        self.assertFalse(self.installer.isProductInstalled("rer.solrpush"))

    def test_browserlayer_removed(self):
        """Test that IRerSolrpushLayer is removed."""
        from rer.solrpush.interfaces import IRerSolrpushLayer
        from plone.browserlayer import utils

        self.assertNotIn(IRerSolrpushLayer, utils.registered_layers())
