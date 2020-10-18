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
from rer.solrpush.testing import RER_SOLRPUSH_FUNCTIONAL_TESTING
from transaction import commit

import unittest


class TestSolrSearch(unittest.TestCase):
    """
    """

    layer = RER_SOLRPUSH_FUNCTIONAL_TESTING

    def setUp(self):
        """
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
        commit()
        self.doc1 = api.content.create(
            container=self.portal,
            type="Document",
            title="First page",
            description="lorem ipsum",
            subject=["foo", "bar"],
        )
        self.doc2 = api.content.create(
            container=self.portal,
            type="Document",
            title="Second page",
            description="lorem ipsum dolor sit amet",
            searchwords="important",
        )
        self.unpublished_doc = api.content.create(
            container=self.portal, type="Document", title="Unpublished page"
        )
        self.published_news = api.content.create(
            container=self.portal,
            type="News Item",
            title="Published News",
            subject=["foo", "news category"],
        )
        self.unpublished_news = api.content.create(
            container=self.portal,
            type="News Item",
            title="Unpublished News",
            subject=["foo"],
        )
        self.event = api.content.create(
            container=self.portal, type="Event", title="Event", subject=["foo"]
        )
        api.content.transition(obj=self.doc1, transition="publish")
        api.content.transition(obj=self.doc2, transition="publish")
        api.content.transition(obj=self.published_news, transition="publish")
        api.content.transition(obj=self.event, transition="publish")
        commit()

    def tearDown(self):
        set_registry_record("active", True, interface=IRerSolrpushSettings)
        #  reset elevate
        set_registry_record(
            "elevate_schema", u"[]", interface=IRerSolrpushSettings
        )
        reset_solr()
        commit()

    def test_search_with_elevate(self):
        doc3 = api.content.create(
            container=self.portal, type="Document", title="Third page"
        )
        doc4 = api.content.create(
            container=self.portal, type="Document", title="Fourth page"
        )
        api.content.transition(obj=doc3, transition="publish")
        api.content.transition(obj=doc4, transition="publish")
        commit()

        solr_results = search(
            query={"SearchableText": "page"}, fl="UID Title"
        ).docs
        self.assertNotEqual(solr_results[0]["UID"], doc4.UID())

        # now let's set an elevate for fourth document
        set_registry_record(
            "elevate_schema",
            u'[{{"text": "page", "ids": ["{}"]}}]'.format(doc4.UID()),
            interface=IRerSolrpushSettings,
        )
        commit()

        solr_results = search(
            query={"SearchableText": "page"}, fl="UID Title"
        ).docs

        self.assertEqual(solr_results[0]["UID"], doc4.UID())