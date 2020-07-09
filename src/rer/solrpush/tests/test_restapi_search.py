# -*- coding: utf-8 -*-
from plone import api
from plone.api.portal import set_registry_record
from plone.app.testing import setRoles
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.app.testing import TEST_USER_ID
from plone.restapi.testing import RelativeSession
from Products.CMFCore.utils import getToolByName
from rer.solrpush.interfaces.settings import IRerSolrpushSettings
from rer.solrpush.testing import RER_SOLRPUSH_API_FUNCTIONAL_TESTING
from rer.solrpush.solr import init_solr_push
from rer.solrpush.solr import reset_solr
from rer.solrpush.solr import search as solr_search

from transaction import commit
import unittest


class SearchBandiTest(unittest.TestCase):

    layer = RER_SOLRPUSH_API_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer["app"]
        self.portal = self.layer["portal"]
        self.portal_url = self.portal.absolute_url()
        self.catalog = getToolByName(self.portal, "portal_catalog")

        self.portal = self.layer["portal"]
        self.request = self.layer["request"]

        self.api_session = RelativeSession(self.portal_url)
        self.api_session.headers.update({"Accept": "application/json"})
        self.api_session.auth = (SITE_OWNER_NAME, SITE_OWNER_PASSWORD)

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

        # publish contents
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
        self.api_session.close()

    def test_search_in_plone_by_default(self):

        response = self.api_session.get("/@search")
        results = response.json()
        self.assertEqual(results[u"items_total"], 6)
        self.assertNotEqual(results[u"items_total"], solr_search(query={}).hits)

    def test_search_in_solr_if_flag_is_set(self):
        set_registry_record("search_with_solr", True, interface=IRerSolrpushSettings)
        commit()

        response = self.api_session.get("/@search")
        results = response.json()
        self.assertEqual(results[u"items_total"], 3)
        self.assertEqual(results[u"items_total"], solr_search(query={}).hits)
        pc = api.portal.get_tool(name="portal_catalog")
        self.assertNotEqual(results[u"items_total"], len(pc()))
