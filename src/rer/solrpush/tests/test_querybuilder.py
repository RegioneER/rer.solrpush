# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from plone import api
from plone.api.portal import set_registry_record
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.namedfile.file import NamedBlobImage
from rer.solrpush.interfaces.settings import IRerSolrpushSettings
from rer.solrpush.utils.solr_common import init_solr_push
from rer.solrpush.utils.solr_common import get_solr_connection
from rer.solrpush.utils import push_to_solr
from rer.solrpush.testing import RER_SOLRPUSH_API_FUNCTIONAL_TESTING
from transaction import commit

import unittest
import os


class TestCollections(unittest.TestCase):
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
        commit()
        # set_registry_record("active", True, interface=IRerSolrpushSettings)
        self.docs = {}
        for i in range(20):
            searchwords = []
            id = "doc-%03d" % i
            if i == 5:
                id = "doc-odd"
                title = "Document %s" % i
                searchwords = ["odd"]
            elif i % 2 == 0:
                title = "Document %s even even" % i
            else:
                title = "Document %s odd odd" % i
            obj = self.docs[i] = api.content.create(
                container=self.portal,
                type="Document",
                id=id,
                title=title,
                searchwords=searchwords,
            )
            # obj.reindexObject(idxs=['Title'])
            api.content.transition(obj=obj, transition="publish")
        for i in range(10):
            id = "event-%03d" % i
            if i == 5:
                id = "event-odd"
                title = "Event %s" % i
            elif i % 2 == 0:
                title = "Event %s even even" % i
            else:
                title = "Event %s odd odd" % i
            obj = self.docs[i] = api.content.create(
                container=self.portal, type="Event", id=id, title=title,
            )
            api.content.transition(obj=obj, transition="publish")

        commit()

    def tearDown(self):
        solr = get_solr_connection()
        solr.delete(q="*:*", commit=True)
        set_registry_record("qf", u"", interface=IRerSolrpushSettings)
        set_registry_record("bq", u"", interface=IRerSolrpushSettings)
        set_registry_record("bf", u"", interface=IRerSolrpushSettings)
        commit()

    def get_results(
        self,
        query,
        batch=True,
        sort_order="",
        b_size=20,
        sort_on="",
        b_start=0,
        limit=1000,
    ):
        querybuilder = api.content.get_view(
            name="querybuilderresults",
            context=self.portal,
            request=self.request,
        )
        params = {
            "query": query,
            "batch": batch,
            "b_start": b_start,
            "b_size": b_size,
            "sort_on": sort_on,
            "sort_order": sort_order,
            "limit": limit,
        }
        return querybuilder(**params)

    def test_by_default_querybuilderresults_search_on_plone_catalog(self):
        query = [
            {
                "i": "portal_type",
                "o": "plone.app.querystring.operation.selection.any",
                "v": ["Event", "Document"],
            },
        ]
        results = self.get_results(query=query)
        self.assertEqual(results.sequence_length, 30)

    def test_querybuilderresults_search_on_solr_if_set(self):
        query = [
            {
                "i": "portal_type",
                "o": "plone.app.querystring.operation.selection.any",
                "v": ["Event", "Document"],
            },
            {
                "i": "searchWithSolr",
                "o": "plone.app.querystring.operation.boolean.isTrue",
                "v": "",
            },
        ]
        results = self.get_results(query=query)

        # events are not indexed on solr
        self.assertEqual(results.sequence_length, 20)

    def test_querybuilderresults_search_on_current_site_by_default(self):
        for i in range(10):
            push_to_solr(
                {
                    "title": "Document {} from another site".format(i),
                    "UID": "foo{}".format(i),
                    "id": "doc-another-site-{}".format(i),
                    "portal_type": "Document",
                    "site_name": "Another site",
                    "url": "http://www.plone.com/doc-{}".format(i),
                }
            )

        query = [
            {
                "i": "portal_type",
                "o": "plone.app.querystring.operation.selection.any",
                "v": ["Event", "Document"],
            },
            {
                "i": "searchWithSolr",
                "o": "plone.app.querystring.operation.boolean.isTrue",
                "v": "",
            },
        ]
        results = self.get_results(query=query)

        self.assertEqual(results.sequence_length, 20)

    def test_querybuilderresults_search_on_multiple_sites_if_set(self):
        for i in range(10):
            push_to_solr(
                {
                    "title": "Document {} from another site".format(i),
                    "UID": "foo{}".format(i),
                    "id": "doc-another-site-{}".format(i),
                    "portal_type": "Document",
                    "site_name": "Another site",
                    "url": "http://www.plone.com/doc-{}".format(i),
                }
            )

        query = [
            {
                "i": "portal_type",
                "o": "plone.app.querystring.operation.selection.any",
                "v": ["Event", "Document"],
            },
            {
                "i": "searchWithSolr",
                "o": "plone.app.querystring.operation.boolean.isTrue",
                "v": "",
            },
            {
                "i": "solr_sites",
                "o": "plone.app.querystring.operation.selection.any",
                "v": ["Another site", "Plone site"],
            },
        ]
        results = self.get_results(query=query)

        self.assertEqual(results.sequence_length, 30)

    def test_querybuilderresults_return_image_tag(self):
        with open(
            os.path.join(os.path.dirname(__file__), "docs", "plone_logo.png"),
            "rb",
        ) as f:
            image_file = NamedBlobImage(
                data=f.read(), filename="plone_logo.png"
            )

        news = api.content.create(
            container=self.portal,
            type="News Item",
            title="News with image",
            image=image_file,
        )
        api.content.transition(obj=news, transition="publish")
        commit()

        query = [
            {
                "i": "portal_type",
                "o": "plone.app.querystring.operation.selection.any",
                "v": ["News Item"],
            },
            {
                "i": "searchWithSolr",
                "o": "plone.app.querystring.operation.boolean.isTrue",
                "v": "",
            },
        ]
        results = self.get_results(query=query)
        self.assertEqual(results.sequence_length, 1)

        item = results[0]
        self.assertEqual(
            item.restrictedTraverse("@@images").tag(),
            '<img src="{}/@@images/image/thumb" alt="News with image" title="News with image">'.format(
                news.absolute_url()
            ),
        )

        self.assertEqual(
            item.restrictedTraverse("@@images").tag(
                alt="alt text", title="custom title"
            ),
            '<img src="{}/@@images/image/thumb" alt="alt text" title="custom title">'.format(
                news.absolute_url()
            ),
        )

        self.assertEqual(
            item.restrictedTraverse("@@images").tag(css_class="custom-css"),
            '<img src="{}/@@images/image/thumb" alt="News with image" title="News with image" class="custom-css">'.format(
                news.absolute_url()
            ),
        )

        self.assertEqual(
            item.restrictedTraverse("@@images").tag(scale="mini"),
            '<img src="{}/@@images/image/mini" alt="News with image" title="News with image">'.format(
                news.absolute_url()
            ),
        )
