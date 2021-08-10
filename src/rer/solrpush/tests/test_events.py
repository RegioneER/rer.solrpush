# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from plone import api
from plone.api.portal import get_registry_record
from plone.api.portal import set_registry_record
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from rer.solrpush.interfaces.settings import IRerSolrpushSettings
from rer.solrpush.utils import init_solr_push
from rer.solrpush.testing import (
    RER_SOLRPUSH_API_FUNCTIONAL_TESTING,
)  # noqa: E501
from transaction import commit
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent
from rer.solrpush.utils import reset_solr

import requests
import unittest

try:
    from Products.CMFPlone.utils import get_installer
except ImportError:
    get_installer = None


class TestSOLRPush(unittest.TestCase):
    """Test that rer.solrpush is properly installed."""

    layer = RER_SOLRPUSH_API_FUNCTIONAL_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        set_registry_record(
            "enabled_types",
            [u"Document", u"File"],
            interface=IRerSolrpushSettings,
        )

    def tearDown(self):
        set_registry_record("active", True, interface=IRerSolrpushSettings)
        reset_solr()

    def test_item_not_indexed_if_solrpush_is_not_ready(self):
        solr_url = get_registry_record("solr_url", IRerSolrpushSettings)
        api.content.create(container=self.portal, type="Document", title="foo")
        commit()
        res = requests.get("{}/select?q=*%3A*&wt=json".format(solr_url)).json()
        self.assertEqual(res["response"]["numFound"], 0)

        init_solr_push()

        api.content.create(container=self.portal, type="Document", title="bar")
        commit()
        res = requests.get("{}/select?q=*%3A*&wt=json".format(solr_url)).json()

        # because initial state id private
        self.assertEqual(res["response"]["numFound"], 0)

        # File types has no wf, so they are published
        api.content.create(
            container=self.portal, type="File", title="bar file"
        )
        commit()
        res = requests.get("{}/select?q=*%3A*&wt=json".format(solr_url)).json()
        self.assertEqual(res["response"]["numFound"], 1)


class TestEvents(unittest.TestCase):
    """Test that rer.solrpush is properly installed."""

    layer = RER_SOLRPUSH_API_FUNCTIONAL_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        set_registry_record(
            "enabled_types",
            [u"Document", u"File"],
            interface=IRerSolrpushSettings,
        )
        init_solr_push()

    def tearDown(self):
        set_registry_record("active", True, interface=IRerSolrpushSettings)
        reset_solr()

    def clean_solr(self):
        solr_url = get_registry_record("solr_url", IRerSolrpushSettings)
        solr_clean_url = "{0}/update?stream.body=<delete><query>*:*</query></delete>&commit=true".format(  # noqa
            solr_url
        )
        requests.get(solr_clean_url)

    def get_solr_results(self):
        solr_url = get_registry_record("solr_url", IRerSolrpushSettings)
        return requests.get(
            "{}/select?q=*%3A*&wt=json".format(solr_url)
        ).json()

    def create_indexed_doc(self):
        published_doc = api.content.create(
            container=self.portal, type="Document", title="foo"
        )
        api.content.transition(obj=published_doc, transition="publish")
        commit()
        return published_doc

    def test_create_indexeable_content(self):
        api.content.create(container=self.portal, type="Document", title="foo")
        commit()
        res = self.get_solr_results()
        self.assertEqual(res["response"]["numFound"], 0)

        api.content.create(container=self.portal, type="File", title="foo")
        commit()
        res = self.get_solr_results()
        self.assertEqual(res["response"]["numFound"], 1)

    def test_create_non_indexeable_content(self):
        # we use images because hte don't have a workflow, like Files.
        api.content.create(container=self.portal, type="Image", title="bara")
        commit()
        res = self.get_solr_results()
        self.assertEqual(res["response"]["numFound"], 0)

    def test_edit_content(self):
        doc = self.create_indexed_doc()
        res = self.get_solr_results()
        self.assertEqual(res["response"]["numFound"], 1)
        res_doc = res["response"]["docs"][0]
        self.assertEqual("foo", res_doc.get("Title", ""))
        self.assertEqual(res_doc.get("Description", ""), "")

        doc.setDescription("foo description")
        notify(ObjectModifiedEvent(doc))
        commit()

        res = self.get_solr_results()
        res_doc = res["response"]["docs"][0]
        self.assertEqual("foo description", res_doc.get("Description", ""))

    def test_change_state(self):
        doc = self.create_indexed_doc()
        res = self.get_solr_results()
        self.assertEqual(res["response"]["numFound"], 1)
        res_doc = res["response"]["docs"][0]
        self.assertEqual("published", res_doc.get("review_state", ""))
        api.content.transition(obj=doc, transition="retract")
        commit()

        res = self.get_solr_results()
        self.assertEqual(res["response"]["numFound"], 0)

    def test_rename_content(self):
        doc = self.create_indexed_doc()
        res = self.get_solr_results()
        self.assertEqual(res["response"]["numFound"], 1)
        res_doc = res["response"]["docs"][0]
        self.assertEqual("foo", res_doc.get("id", ""))
        api.content.rename(obj=doc, new_id="bar")
        commit()

        res = self.get_solr_results()
        res_doc = res["response"]["docs"][0]
        self.assertEqual("bar", res_doc.get("id", ""))

    def test_delete_content(self):
        doc = self.create_indexed_doc()
        res = self.get_solr_results()
        self.assertEqual(res["response"]["numFound"], 1)
        api.content.delete(obj=doc)
        commit()

        res = self.get_solr_results()
        self.assertEqual(res["response"]["numFound"], 0)
