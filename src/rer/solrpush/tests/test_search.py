# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from plone import api
from plone.api.portal import set_registry_record
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from rer.solrpush.interfaces.settings import IRerSolrpushSettings
from rer.solrpush.testing import RER_SOLRPUSH_API_FUNCTIONAL_TESTING  # noqa: E501
from rer.solrpush.utils import init_solr_push
from rer.solrpush.utils import reset_solr
from rer.solrpush.utils import search
from rer.solrpush.utils.solr_search import escape_special_characters
from transaction import commit

import unittest


class TestSearch(unittest.TestCase):
    """Test show in search field behavior."""

    layer = RER_SOLRPUSH_API_FUNCTIONAL_TESTING

    def setUp(self):
        """
        We create objects before initializing solr settings, so solr core is
        always empty on setUp.
        """
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]

        self.request._rest_cors_preflight = True
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        set_registry_record(
            "enabled_types",
            ["Document", "News Item"],
            interface=IRerSolrpushSettings,
        )
        init_solr_push()
        # set_registry_record("active", True, interface=IRerSolrpushSettings)
        self.docs = {}
        for i in range(20):
            id = "doc-%03d" % i
            if i == 5:
                id = "odd"
                title = "Document %s" % i
            elif i % 2 == 0:
                title = "Document %s even even" % i
            else:
                title = "Document %s odd odd" % i
            obj = self.docs[i] = api.content.create(
                container=self.portal,
                type="Document",
                id=id,
                title=title,
            )
            # obj.reindexObject(idxs=['Title'])
            api.content.transition(obj=obj, transition="publish")
        commit()

    def tearDown(self):
        reset_solr(all=True)
        set_registry_record("qf", "", interface=IRerSolrpushSettings)
        set_registry_record("bq", "", interface=IRerSolrpushSettings)
        set_registry_record("bf", "", interface=IRerSolrpushSettings)
        commit()

    def test_all_items(self):
        solr_results = search(query={}, fl="UID")
        self.assertEqual(solr_results.hits, len(self.docs))

    def test_search_odd(self):
        solr_results = search(query={"SearchableText": "odd"}, fl="UID")
        self.assertEqual(solr_results.hits, len(self.docs) / 2)

    def test_search_qf(self):
        solr_results = search(query={"": "odd"}, fl=["UID", "id", "Title"])
        self.assertEqual(solr_results.hits, len(self.docs) / 2)
        self.assertNotEqual(solr_results.docs[0]["id"], "odd")

        set_registry_record(
            "qf",
            "id^1000.0 SearchableText^1.0",
            interface=IRerSolrpushSettings,
        )
        commit()
        solr_results = search(query={"": "odd"}, fl=["UID", "id", "Title"])
        self.assertEqual(solr_results.hits, len(self.docs) / 2)
        self.assertEqual(solr_results.docs[0]["id"], "odd")

    def test_search_bq(self):
        solr_results = search(query={"": "odd"}, fl=["UID", "id", "Title"])
        self.assertEqual(solr_results.hits, len(self.docs) / 2)
        self.assertNotEqual(solr_results.docs[0]["id"], "odd")

        set_registry_record("bq", "id:odd", interface=IRerSolrpushSettings)
        commit()

        solr_results = search(query={"": "odd"}, fl=["UID", "id", "Title"])
        self.assertEqual(solr_results.hits, len(self.docs) / 2)
        self.assertEqual(solr_results.docs[0]["id"], "odd")

    def test_escape_chars(self):
        self.assertEqual(escape_special_characters("*:*", False), "\\*\\:\\*")
        self.assertEqual(escape_special_characters("* : *", True), '"\\* \\: \\*"')
