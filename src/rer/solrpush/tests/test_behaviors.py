# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from plone import api
from plone.api.portal import set_registry_record
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from rer.solrpush.interfaces.settings import IRerSolrpushSettings
from rer.solrpush.utils import init_solr_push
from rer.solrpush.utils import reset_solr
from rer.solrpush.utils import search
from rer.solrpush.testing import (
    RER_SOLRPUSH_API_FUNCTIONAL_TESTING,
)  # noqa: E501
from transaction import commit

import unittest


class TestShowInSearch(unittest.TestCase):
    """Test show in search field behavior."""

    layer = RER_SOLRPUSH_API_FUNCTIONAL_TESTING

    def setUp(self):
        """
        We create objects before initializing solr settings, so solr core is
        always empty on setUp.
        """
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        set_registry_record(
            "enabled_types",
            [u"Document", u"News Item"],
            interface=IRerSolrpushSettings,
        )
        init_solr_push()
        self.document = api.content.create(
            container=self.portal, type="Document", title="Document foo"
        )
        api.content.transition(obj=self.document, transition="publish")
        self.news = api.content.create(
            container=self.portal, type="News Item", title="News bar"
        )
        api.content.transition(obj=self.news, transition="publish")
        commit()

    def tearDown(self):
        reset_solr()
        commit()

    def test_items_are_indexed_by_default(self):
        solr_results = search(query={"*": "*", "b_size": 100000}, fl="UID")
        self.assertEqual(solr_results.hits, 2)

    def test_items_are_unindexed_when_set_false(self):
        self.document.showinsearch = False
        self.document.reindexObject()
        commit()
        solr_results = search(query={"*": "*", "b_size": 100000}, fl="UID")
        self.assertEqual(solr_results.hits, 1)
