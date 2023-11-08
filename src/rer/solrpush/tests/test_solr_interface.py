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
from rer.solrpush.utils import push_to_solr
from rer.solrpush.utils import remove_from_solr
from rer.solrpush.testing import RER_SOLRPUSH_API_FUNCTIONAL_TESTING
import time
from transaction import commit

import unittest


class TestSolrIndexActions(unittest.TestCase):
    """Test that rer.solrpush is properly installed."""

    layer = RER_SOLRPUSH_API_FUNCTIONAL_TESTING

    def setUp(self):
        """"""
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        set_registry_record(
            "enabled_types", [u"Document"], interface=IRerSolrpushSettings
        )
        self.published_doc = api.content.create(
            container=self.portal, type="Document", title="Published Document"
        )
        api.content.transition(obj=self.published_doc, transition="publish")
        self.unpublished_doc = api.content.create(
            container=self.portal,
            type="Document",
            title="Unpublished Document",
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
        solr_results = search(
            query={"*": "*", "b_size": 100000}, fl="UID Description"
        )
        self.assertEqual(solr_results.hits, 1)
        self.assertEqual(solr_results.docs[0]["UID"], self.published_doc.UID())
        self.assertEqual(solr_results.docs[0].get("Description", ""), "")

        self.published_doc.setDescription("foo description")
        push_to_solr(self.published_doc)
        solr_results = search(
            query={"*": "*", "b_size": 100000}, fl="UID Description"
        )
        self.assertEqual(solr_results.hits, 1)
        self.assertEqual(solr_results.docs[0]["UID"], self.published_doc.UID())
        self.assertIn("Description", solr_results.docs[0])
        self.assertEqual(
            solr_results.docs[0]["Description"], "foo description"
        )

    def test_remove_from_solr(self):
        solr_results = search(query={"*": "*", "b_size": 100000}, fl="UID")
        self.assertEqual(solr_results.hits, 0)

        api.content.transition(obj=self.unpublished_doc, transition="publish")
        # commit()
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
        self.assertEqual(
            solr_results.docs[0]["UID"], self.unpublished_doc.UID()
        )

    def test_reset_solr(self):
        solr_results = search(query={"*": "*", "b_size": 100000}, fl="UID")
        self.assertEqual(solr_results.hits, 0)

        api.content.transition(obj=self.unpublished_doc, transition="publish")
        # commit()
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


class TestSolrSearch(unittest.TestCase):
    """"""

    layer = RER_SOLRPUSH_API_FUNCTIONAL_TESTING

    def setUp(self):
        """"""
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        set_registry_record(
            "enabled_types",
            [u"Document", u"News Item"],
            interface=IRerSolrpushSettings,
        )
        #  initialize solr push, so solr will be populated automatically
        # on commits
        init_solr_push()
        commit()
        self.doc1 = api.content.create(
            container=self.portal,
            type="Document",
            title="First Document",
            description="lorem ipsum",
            subject=["foo", "bar"],
        )
        self.doc2 = api.content.create(
            container=self.portal,
            type="Document",
            title="Second Document",
            description="lorem ipsum dolor sit amet",
        )
        self.unpublished_doc = api.content.create(
            container=self.portal,
            type="Document",
            title="Unpublished Document",
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
        # commit()
        api.content.transition(obj=self.doc2, transition="publish")
        # commit()
        api.content.transition(obj=self.published_news, transition="publish")
        # commit()
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
        solr_results = search(query={"SearchableText": "Document"})
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
        """"""
        # update modification date
        time.sleep(1)
        self.doc2.reindexObject()
        commit()
        solr_results = search(
            query={"portal_type": "Document", "sort_on": "modified"}
        )
        self.assertEqual(solr_results.hits, 2)
        self.assertEqual(solr_results.docs[0]["UID"], self.doc1.UID())
        self.assertEqual(solr_results.docs[1]["UID"], self.doc2.UID())
        solr_results = search(
            query={
                "portal_type": "Document",
                "sort_on": "modified",
                "sort_order": "reverse",
            }
        )
        self.assertEqual(solr_results.hits, 2)
        self.assertEqual(solr_results.docs[0]["UID"], self.doc2.UID())
        self.assertEqual(solr_results.docs[1]["UID"], self.doc1.UID())
