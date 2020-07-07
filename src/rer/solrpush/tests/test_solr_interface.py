# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from plone import api
from plone.api.portal import set_registry_record
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from rer.solrpush.interfaces.settings import IRerSolrpushSettings
from rer.solrpush.solr import init_solr_push
from rer.solrpush.solr import reset_solr
from rer.solrpush.solr import push_to_solr
from rer.solrpush.solr import remove_from_solr
from rer.solrpush.solr import search
from rer.solrpush.testing import RER_SOLRPUSH_FUNCTIONAL_TESTING
from transaction import commit

import unittest


class TestSolrIndexActions(unittest.TestCase):
    """Test that rer.solrpush is properly installed."""

    layer = RER_SOLRPUSH_FUNCTIONAL_TESTING

    def setUp(self):
        """
        """
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        set_registry_record(
            "enabled_types", ["Document"], interface=IRerSolrpushSettings
        )
        self.published_doc = api.content.create(
            container=self.portal, type="Document", title="Published Document"
        )
        api.content.transition(obj=self.published_doc, transition="publish")
        self.unpublished_doc = api.content.create(
            container=self.portal, type="Document", title="Unpublished Document"
        )
        self.published_news = api.content.create(
            container=self.portal, type="News Item", title="Published News"
        )
        self.unpublished_news = api.content.create(
            container=self.portal, type="News Item", title="Unpublished News"
        )
        api.content.transition(obj=self.published_news, transition="publish")
        init_solr_push()

    def tearDown(self):
        set_registry_record("active", True, interface=IRerSolrpushSettings)
        reset_solr()

    def test_push_to_solr(self):
        solr_results = search(query={"*": "*", "b_size": 100000}, fl="UID")
        self.assertEqual(solr_results.hits, 0)

        # try to push an indexable and published content
        push_to_solr(self.published_doc)
        solr_results = search(query={"*": "*", "b_size": 100000}, fl="UID")
        self.assertEqual(solr_results.hits, 1)
        self.assertEqual(solr_results.docs[0]["UID"], self.published_doc.UID())

        # try to push an indexable and private content
        push_to_solr(self.unpublished_doc)
        solr_results = search(query={"*": "*", "b_size": 100000}, fl="UID")
        self.assertEqual(solr_results.hits, 1)
        self.assertEqual(solr_results.docs[0]["UID"], self.published_doc.UID())

        # try to push a non indexable published content
        push_to_solr(self.published_news)
        solr_results = search(query={"*": "*", "b_size": 100000}, fl="UID")
        self.assertEqual(solr_results.hits, 1)
        self.assertEqual(solr_results.docs[0]["UID"], self.published_doc.UID())

        # try to push a non indexable private content
        push_to_solr(self.unpublished_news)
        solr_results = search(query={"*": "*", "b_size": 100000}, fl="UID")
        self.assertEqual(solr_results.hits, 1)
        self.assertEqual(solr_results.docs[0]["UID"], self.published_doc.UID())

    def test_update_content(self):
        push_to_solr(self.published_doc)
        solr_results = search(query={"*": "*", "b_size": 100000}, fl="UID Description")
        self.assertEqual(solr_results.hits, 1)
        self.assertEqual(solr_results.docs[0]["UID"], self.published_doc.UID())
        self.assertEqual(solr_results.docs[0].get("Description", ""), "")

        self.published_doc.description = "foo description"
        push_to_solr(self.published_doc)
        solr_results = search(query={"*": "*", "b_size": 100000}, fl="UID Description")
        self.assertEqual(solr_results.hits, 1)
        self.assertEqual(solr_results.docs[0]["UID"], self.published_doc.UID())
        self.assertIn("Description", solr_results.docs[0])
        self.assertEqual(solr_results.docs[0]["Description"], "foo description")

    def test_remove_from_solr(self):
        solr_results = search(query={"*": "*", "b_size": 100000}, fl="UID")
        self.assertEqual(solr_results.hits, 0)

        api.content.transition(obj=self.unpublished_doc, transition="publish")
        commit()
        # try to push an indexable and published content
        push_to_solr(self.published_doc)
        push_to_solr(self.unpublished_doc)
        solr_results = search(query={"*": "*", "b_size": 100000}, fl="UID")
        self.assertEqual(solr_results.hits, 2)
        self.assertEqual(solr_results.docs[0]["UID"], self.published_doc.UID())

        # try to remove content from solr
        remove_from_solr(uid=self.published_doc.UID())
        solr_results = search(query={"*": "*", "b_size": 100000}, fl="UID")
        self.assertEqual(solr_results.hits, 1)
        self.assertEqual(solr_results.docs[0]["UID"], self.unpublished_doc.UID())

    def test_reset_solr(self):
        solr_results = search(query={"*": "*", "b_size": 100000}, fl="UID")
        self.assertEqual(solr_results.hits, 0)

        api.content.transition(obj=self.unpublished_doc, transition="publish")
        commit()
        # try to push an indexable and published content
        push_to_solr(self.published_doc)
        push_to_solr(self.unpublished_doc)
        solr_results = search(query={"*": "*", "b_size": 100000}, fl="UID")
        self.assertEqual(solr_results.hits, 2)
        self.assertEqual(solr_results.docs[0]["UID"], self.published_doc.UID())

        # cleanup catalog
        reset_solr()
        solr_results = search(query={"*": "*", "b_size": 100000}, fl="UID")
        self.assertEqual(solr_results.hits, 0)
