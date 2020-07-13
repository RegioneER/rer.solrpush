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
            "enabled_types", ["Document", "News Item"], interface=IRerSolrpushSettings
        )
        #  initialize solr push, so solr will be populated automatically
        # on commits
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
        commit()
        api.content.transition(obj=self.doc2, transition="publish")
        commit()
        api.content.transition(obj=self.published_news, transition="publish")
        commit()
        api.content.transition(obj=self.event, transition="publish")
        commit()

    def tearDown(self):
        set_registry_record("active", True, interface=IRerSolrpushSettings)
        reset_solr()

    def test_search_all(self):
        solr_results = search(query={"*": "*"})
        # only published and indexable contents are on solr
        self.assertEqual(solr_results.hits, 3)
        uids = [x["UID"] for x in solr_results.docs]
        self.assertIn(self.doc1.UID(), uids)
        self.assertIn(self.doc2.UID(), uids)
        self.assertIn(self.published_news.UID(), uids)
        self.assertNotIn(self.unpublished_doc.UID(), uids)
        self.assertNotIn(self.unpublished_news.UID(), uids)
        self.assertNotIn(self.event.UID(), uids)

    def test_search_q(self):
        solr_results = search(query={"SearchableText": "page"})
        self.assertEqual(solr_results.hits, 2)
        uids = [x["UID"] for x in solr_results.docs]
        self.assertIn(self.doc1.UID(), uids)
        self.assertIn(self.doc2.UID(), uids)
        self.assertNotIn(self.published_news.UID(), uids)
        self.assertNotIn(self.unpublished_doc.UID(), uids)
        self.assertNotIn(self.unpublished_news.UID(), uids)
        self.assertNotIn(self.event.UID(), uids)

        solr_results = search(query={"SearchableText": "lorem ipsum"})
        self.assertEqual(solr_results.hits, 2)
        uids = [x["UID"] for x in solr_results.docs]
        self.assertIn(self.doc1.UID(), uids)
        self.assertIn(self.doc2.UID(), uids)

        solr_results = search(query={"SearchableText": "lorem amet"})
        self.assertEqual(solr_results.hits, 1)
        uids = [x["UID"] for x in solr_results.docs]
        self.assertNotIn(self.doc1.UID(), uids)
        self.assertIn(self.doc2.UID(), uids)

        solr_results = search(query={"SearchableText": "lorem OR amet"})
        self.assertEqual(solr_results.hits, 2)
        uids = [x["UID"] for x in solr_results.docs]
        self.assertIn(self.doc1.UID(), uids)
        self.assertIn(self.doc2.UID(), uids)

    def test_search_fq(self):
        #  same result if we search by portal_type
        solr_results = search(query={"portal_type": "Document"})
        self.assertEqual(solr_results.hits, 2)
        uids = [x["UID"] for x in solr_results.docs]
        self.assertIn(self.doc1.UID(), uids)
        self.assertIn(self.doc2.UID(), uids)
        self.assertNotIn(self.published_news.UID(), uids)
        self.assertNotIn(self.unpublished_doc.UID(), uids)
        self.assertNotIn(self.unpublished_news.UID(), uids)
        self.assertNotIn(self.event.UID(), uids)

        solr_results = search(query={"portal_type": "News Item"})
        self.assertEqual(solr_results.hits, 1)
        uids = [x["UID"] for x in solr_results.docs]
        self.assertNotIn(self.doc1.UID(), uids)
        self.assertNotIn(self.doc2.UID(), uids)
        self.assertIn(self.published_news.UID(), uids)
        self.assertNotIn(self.unpublished_doc.UID(), uids)
        self.assertNotIn(self.unpublished_news.UID(), uids)
        self.assertNotIn(self.event.UID(), uids)

        solr_results = search(query={"Subject": "foo"})
        self.assertEqual(solr_results.hits, 2)
        uids = [x["UID"] for x in solr_results.docs]
        self.assertIn(self.doc1.UID(), uids)
        self.assertNotIn(self.doc2.UID(), uids)
        self.assertIn(self.published_news.UID(), uids)
        self.assertNotIn(self.unpublished_doc.UID(), uids)
        self.assertNotIn(self.unpublished_news.UID(), uids)
        self.assertNotIn(self.event.UID(), uids)

        solr_results = search(query={"Subject": "bar"})
        self.assertEqual(solr_results.hits, 1)
        uids = [x["UID"] for x in solr_results.docs]
        self.assertIn(self.doc1.UID(), uids)
        self.assertNotIn(self.doc2.UID(), uids)
        self.assertNotIn(self.published_news.UID(), uids)
        self.assertNotIn(self.unpublished_doc.UID(), uids)
        self.assertNotIn(self.unpublished_news.UID(), uids)
        self.assertNotIn(self.event.UID(), uids)

        solr_results = search(query={"Subject": ["foo", "bar"]})
        self.assertEqual(solr_results.hits, 2)
        uids = [x["UID"] for x in solr_results.docs]
        self.assertIn(self.doc1.UID(), uids)
        self.assertNotIn(self.doc2.UID(), uids)
        self.assertIn(self.published_news.UID(), uids)
        self.assertNotIn(self.unpublished_doc.UID(), uids)
        self.assertNotIn(self.unpublished_news.UID(), uids)
        self.assertNotIn(self.event.UID(), uids)

        solr_results = search(query={"Subject": ["news category"]})
        self.assertEqual(solr_results.hits, 1)
        uids = [x["UID"] for x in solr_results.docs]
        self.assertNotIn(self.doc1.UID(), uids)
        self.assertNotIn(self.doc2.UID(), uids)
        self.assertIn(self.published_news.UID(), uids)
        self.assertNotIn(self.unpublished_doc.UID(), uids)
        self.assertNotIn(self.unpublished_news.UID(), uids)
        self.assertNotIn(self.event.UID(), uids)

    def test_search_fl(self):
        """
        with fl we can select which fields solr returns for results
        """
        solr_results = search(query={"*": "*"})
        self.assertEqual(solr_results.hits, 3)
        for doc in solr_results.docs:
            self.assertIn("UID", list(doc.keys()))
            self.assertIn("Title", list(doc.keys()))

        solr_results = search(query={"*": "*"}, fl="UID")
        self.assertEqual(solr_results.hits, 3)
        for doc in solr_results.docs:
            self.assertIn("UID", list(doc.keys()))
            self.assertNotIn("Title", list(doc.keys()))

        solr_results = search(query={"*": "*"}, fl="UID Subject")
        self.assertEqual(solr_results.hits, 3)
        for doc in solr_results.docs:
            self.assertIn("UID", list(doc.keys()))
            self.assertNotIn("Title", list(doc.keys()))
            if not api.content.get(UID=doc["UID"]).Subject():
                self.assertNotIn("Subject", list(doc.keys()))
            else:
                self.assertIn("Subject", list(doc.keys()))

    def test_search_sort_on(self):
        """
        """
        # update modification date
        self.doc2.reindexObject()
        commit()
        solr_results = search(query={"portal_type": "Document", "sort_on": "id"})
        self.assertEqual(solr_results.hits, 2)
        self.assertEqual(solr_results.docs[0]["UID"], self.doc1.UID())
        self.assertEqual(solr_results.docs[1]["UID"], self.doc2.UID())
        solr_results = search(
            query={"portal_type": "Document", "sort_on": "id", "sort_order": "reverse"}
        )
        self.assertEqual(solr_results.hits, 2)
        self.assertEqual(solr_results.docs[0]["UID"], self.doc2.UID())
        self.assertEqual(solr_results.docs[1]["UID"], self.doc1.UID())

    def test_search_with_custom_query(self):
        doc3 = api.content.create(
            container=self.portal, type="Document", title="Third page"
        )
        doc4 = api.content.create(
            container=self.portal, type="Document", title="Fourth page"
        )
        api.content.transition(obj=doc3, transition="publish")
        commit()
        api.content.transition(obj=doc4, transition="publish")
        commit()

        solr_results = search(query={"SearchableText": "page"}, fl="UID Title").docs
        self.assertNotEqual(solr_results[0]["UID"], self.doc2.UID())

        # now let's set a custom query that elevates items with a specific searchword
        set_registry_record(
            "custom_query",
            u"SearchableText:({value}) OR searchwords:(important)^1000",
            interface=IRerSolrpushSettings,
        )
        commit()

        solr_results = search(query={"SearchableText": "page"}, fl="UID Title").docs

        self.assertEqual(solr_results[0]["UID"], self.doc2.UID())

    def test_search_with_elevate(self):
        doc3 = api.content.create(
            container=self.portal, type="Document", title="Third page"
        )
        doc4 = api.content.create(
            container=self.portal, type="Document", title="Fourth page"
        )
        api.content.transition(obj=doc3, transition="publish")
        commit()
        api.content.transition(obj=doc4, transition="publish")
        commit()
        solr_results = search(query={"SearchableText": "page"}, fl="UID Title").docs
        self.assertNotEqual(solr_results[0]["UID"], doc4.UID())

        # now let's set an elevate for third document
        set_registry_record(
            "elevate_schema",
            u'[{{"text": "page", "ids": ["{}"]}}]'.format(doc4.UID()),
            interface=IRerSolrpushSettings,
        )
        set_registry_record("custom_query", u"", interface=IRerSolrpushSettings)
        commit()
        solr_results = search(query={"SearchableText": "page"}, fl="UID Title").docs

        self.assertEqual(solr_results[0]["UID"], doc4.UID())

        # reset elevate
        set_registry_record("elevate_schema", u"[]", interface=IRerSolrpushSettings)
        commit()
