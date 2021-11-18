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
from rer.solrpush.utils import init_solr_push
from rer.solrpush.utils import reset_solr

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
            "enabled_types",
            [u"Document", u"News Item"],
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

        # publish contents
        api.content.transition(obj=self.doc1, transition="publish")
        api.content.transition(obj=self.doc2, transition="publish")
        api.content.transition(obj=self.published_news, transition="publish")
        api.content.transition(obj=self.event, transition="publish")
        commit()

    def tearDown(self):
        set_registry_record("active", True, interface=IRerSolrpushSettings)
        reset_solr()
        commit()

    def test_search_works(self):

        solr_response = self.api_session.get("/@solr-search")
        plone_response = self.api_session.get("/@search")
        solr_results = solr_response.json()
        plone_results = plone_response.json()
        self.assertEqual(plone_results[u"items_total"], 6)
        self.assertEqual(solr_results[u"items_total"], 3)
