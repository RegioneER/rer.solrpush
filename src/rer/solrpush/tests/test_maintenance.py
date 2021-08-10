# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from AccessControl import Unauthorized
from plone import api
from plone.api.portal import get_registry_record
from plone.api.portal import set_registry_record
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.protect.authenticator import createToken
from rer.solrpush.interfaces.settings import IRerSolrpushSettings
from rer.solrpush.utils import init_solr_push
from rer.solrpush.utils import reset_solr
from rer.solrpush.utils import search
from rer.solrpush.testing import (
    RER_SOLRPUSH_API_FUNCTIONAL_TESTING,
)  # noqa: E501
from transaction import commit

import unittest

try:
    from Products.CMFPlone.utils import get_installer
except ImportError:
    get_installer = None


class TestMaintenance(unittest.TestCase):
    """Test that rer.solrpush is properly installed."""

    layer = RER_SOLRPUSH_API_FUNCTIONAL_TESTING

    def setUp(self):
        """
        We create objects before initializing solr settings, so solr core is
        always empty on setUp.
        """
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        set_registry_record("active", False, interface=IRerSolrpushSettings)
        set_registry_record(
            "enabled_types", [u"Document"], interface=IRerSolrpushSettings
        )
        get_registry_record("enabled_types", interface=IRerSolrpushSettings)
        self.published_doc = api.content.create(
            container=self.portal, type="Document", title="Published Document"
        )
        api.content.transition(obj=self.published_doc, transition="publish")
        self.unpublished_doc = api.content.create(
            container=self.portal,
            type="Document",
            title="Unpublished Document",
        )
        self.news = api.content.create(
            container=self.portal, type="News Item", title="Unpublished News"
        )
        # flush catalog queue
        api.portal.get_tool("portal_catalog")()  # or commit()
        init_solr_push()
        set_registry_record("active", True, interface=IRerSolrpushSettings)

    def tearDown(self):
        # set_registry_record('active', True, interface=IRerSolrpushSettings)
        reset_solr()

    @property
    def reindex_view(self):
        self.request.form["_authenticator"] = createToken()
        return api.content.get_view(
            name="do-reindex", context=self.portal, request=self.request
        )

    @property
    def sync_view(self):
        self.request.form["_authenticator"] = createToken()
        return api.content.get_view(
            name="do-sync", context=self.portal, request=self.request
        )

    def test_maintenance_do_reindex_is_protected(self):
        reindex_view = api.content.get_view(
            name="do-reindex", context=self.portal, request=self.request
        )
        with self.assertRaises(Unauthorized):
            reindex_view()

    def test_maintenance_do_sync_is_protected(self):
        sync_view = api.content.get_view(
            name="do-sync", context=self.portal, request=self.request
        )
        with self.assertRaises(Unauthorized):
            sync_view()

    def test_maintenance_reindex(self):
        solr_results = search(query={"*": "*", "b_size": 100000}, fl="UID")
        self.assertEqual(solr_results.hits, 0)
        self.reindex_view()
        solr_results = search(query={"*": "*", "b_size": 100000}, fl="UID")
        self.assertEqual(solr_results.hits, 1)
        self.assertEqual(solr_results.docs[0]["UID"], self.published_doc.UID())

        # now, disable solr indexer and publish other two items
        set_registry_record("active", False, interface=IRerSolrpushSettings)
        api.content.transition(obj=self.news, transition="publish")
        api.content.transition(obj=self.unpublished_doc, transition="publish")
        commit()
        solr_results = search(query={"*": "*", "b_size": 100000}, fl="UID")
        self.assertEqual(solr_results.hits, 1)

        # now, enable and reindex
        set_registry_record("active", True, interface=IRerSolrpushSettings)
        self.reindex_view()
        solr_results = search(query={"*": "*", "b_size": 100000}, fl="UID")
        # news items are not enabled
        self.assertEqual(solr_results.hits, 2)
        self.assertEqual(
            set(doc["UID"] for doc in solr_results.docs),
            set([self.published_doc.UID(), self.unpublished_doc.UID()]),
        )

    def test_maintenance_reindex_with_unwanted_types(self):
        self.reindex_view()
        solr_results = search(query={"*": "*", "b_size": 100000}, fl="UID")
        self.assertEqual(solr_results.hits, 1)

        set_registry_record(
            "enabled_types",
            [u"Document", u"News Item"],
            interface=IRerSolrpushSettings,
        )
        api.content.transition(obj=self.news, transition="publish")
        api.content.transition(obj=self.unpublished_doc, transition="publish")
        commit()
        solr_results = search(
            query={"*": "*", "b_size": 100000}, fl="UID,portal_type"
        )
        self.assertEqual(solr_results.hits, 3)

        set_registry_record(
            "enabled_types", [u"Document"], interface=IRerSolrpushSettings
        )
        self.reindex_view()
        solr_results = search(query={"*": "*", "b_size": 100000}, fl="UID")
        # News isn't removed because reindex view only reindex values from
        # Plone
        self.assertEqual(solr_results.hits, 3)

    def test_maintenance_sync(self):
        api.content.transition(obj=self.news, transition="publish")
        api.content.transition(obj=self.unpublished_doc, transition="publish")
        set_registry_record(
            "enabled_types",
            [u"Document", u"News Item"],
            interface=IRerSolrpushSettings,
        )
        self.reindex_view()
        solr_results = search(query={"*": "*", "b_size": 100000}, fl="UID")
        self.assertEqual(solr_results.hits, 3)

        set_registry_record(
            "enabled_types", [u"Document"], interface=IRerSolrpushSettings
        )
        self.sync_view()
        solr_results = search(query={"*": "*", "b_size": 100000}, fl="UID")
        self.assertEqual(solr_results.hits, 2)
