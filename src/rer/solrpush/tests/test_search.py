# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from plone import api
from plone.api.portal import set_registry_record
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from rer.solrpush.interfaces.settings import IRerSolrpushSettings
from rer.solrpush.solr import init_solr_push
from rer.solrpush.solr import reset_solr
from rer.solrpush.solr import search
from rer.solrpush.testing import RER_SOLRPUSH_FUNCTIONAL_TESTING  # noqa: E501
from transaction import commit

import unittest


class TestSearch(unittest.TestCase):
    """Test show in search field behavior."""

    layer = RER_SOLRPUSH_FUNCTIONAL_TESTING

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
            ["Document", "News Item"],
            interface=IRerSolrpushSettings,
        )
        init_solr_push()
        # set_registry_record("active", True, interface=IRerSolrpushSettings)
        self.document = {}
        for i in range(10):
            self.document[i] = api.content.create(
                container=self.portal,
                type="Document",
                id="doc-%03d" % i,
                title="Document %s" % i,
            )
            api.content.transition(obj=self.document[i], transition="publish")
        commit()

    def tearDown(self):
        reset_solr()
        commit()

    def test_items_are_indexed_by_default(self):
        solr_results = search(query={"*": "*", "b_size": 100000}, fl="UID")
        self.assertEqual(solr_results.hits, 10)
