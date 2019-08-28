# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from rer.solrpush.testing import RER_SOLRPUSH_FUNCTIONAL_TESTING  # noqa: E501
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.api.portal import set_registry_record
from plone.api.portal import get_registry_record
from rer.solrpush.interfaces import IRerSolrpushSettings
from plone import api
from rer.solrpush.solr import init_solr_push
from transaction import commit
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent

import requests
import unittest

try:
    from Products.CMFPlone.utils import get_installer
except ImportError:
    get_installer = None


class TestSOLRPush(unittest.TestCase):
    """Test that rer.solrpush is properly installed."""

    layer = RER_SOLRPUSH_FUNCTIONAL_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        set_registry_record(
            'enabled_types', ['Document'], interface=IRerSolrpushSettings
        )

    def tearDown(self):
        solr_url = get_registry_record('solr_url', IRerSolrpushSettings)
        solr_clean_url = "{0}/update?stream.body=<delete><query>*:*</query></delete>&commit=true".format(  # noqa
            solr_url
        )
        requests.get(solr_clean_url)

    def test_item_not_indexed_if_solrpush_is_not_ready(self):
        solr_url = get_registry_record('solr_url', IRerSolrpushSettings)
        api.content.create(container=self.portal, type='Document', title='foo')
        commit()
        res = requests.get('{}/select?q=*%3A*&wt=json'.format(solr_url)).json()
        self.assertEquals(res['response']['numFound'], 0)

        init_solr_push()

        api.content.create(container=self.portal, type='Document', title='bar')
        commit()
        res = requests.get('{}/select?q=*%3A*&wt=json'.format(solr_url)).json()
        self.assertEquals(res['response']['numFound'], 1)


class TestEvents(unittest.TestCase):
    """Test that rer.solrpush is properly installed."""

    layer = RER_SOLRPUSH_FUNCTIONAL_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        set_registry_record(
            'enabled_types', ['Document'], interface=IRerSolrpushSettings
        )
        init_solr_push()

    def tearDown(self):
        self.clean_solr()

    def clean_solr(self):
        solr_url = get_registry_record('solr_url', IRerSolrpushSettings)
        solr_clean_url = "{0}/update?stream.body=<delete><query>*:*</query></delete>&commit=true".format(  # noqa
            solr_url
        )
        requests.get(solr_clean_url)

    def get_solr_results(self):
        solr_url = get_registry_record('solr_url', IRerSolrpushSettings)
        return requests.get(
            '{}/select?q=*%3A*&wt=json'.format(solr_url)
        ).json()

    def test_create_indexeable_content(self):
        api.content.create(container=self.portal, type='Document', title='foo')
        commit()
        res = self.get_solr_results()
        self.assertEquals(res['response']['numFound'], 1)

    def test_create_non_indexeable_content(self):
        api.content.create(container=self.portal, type='Event', title='bar')
        commit()
        res = self.get_solr_results()
        self.assertEquals(res['response']['numFound'], 0)

    def test_edit_content(self):
        doc = api.content.create(
            container=self.portal, type='Document', title='foo'
        )
        commit()
        res = self.get_solr_results()
        self.assertEquals(res['response']['numFound'], 1)
        res_doc = res['response']['docs'][0]
        self.assertEqual('foo', res_doc.get('Title', ''))
        self.assertNotIn('Description', res_doc)
        doc.description = 'foo description'

        notify(ObjectModifiedEvent(doc))
        commit()

        res = self.get_solr_results()
        res_doc = res['response']['docs'][0]
        self.assertEqual('foo description', res_doc.get('Description', ''))

    def test_change_state(self):
        doc = api.content.create(
            container=self.portal, type='Document', title='foo'
        )
        commit()
        res = self.get_solr_results()
        self.assertEquals(res['response']['numFound'], 1)
        res_doc = res['response']['docs'][0]
        self.assertEqual('private', res_doc.get('review_state', ''))
        api.content.transition(obj=doc, transition='publish')
        commit()

        res = self.get_solr_results()
        res_doc = res['response']['docs'][0]
        self.assertEqual('published', res_doc.get('review_state', ''))

    def test_rename_content(self):
        doc = api.content.create(
            container=self.portal, type='Document', title='foo'
        )
        commit()
        res = self.get_solr_results()
        self.assertEquals(res['response']['numFound'], 1)
        res_doc = res['response']['docs'][0]
        self.assertEqual('foo', res_doc.get('id', ''))
        api.content.rename(obj=doc, new_id='bar')
        commit()

        res = self.get_solr_results()
        res_doc = res['response']['docs'][0]
        self.assertEqual('bar', res_doc.get('id', ''))

    def test_delete_content(self):
        doc = api.content.create(
            container=self.portal, type='Document', title='foo'
        )
        commit()
        res = self.get_solr_results()
        self.assertEquals(res['response']['numFound'], 1)
        api.content.delete(obj=doc)
        commit()

        res = self.get_solr_results()
        self.assertEquals(res['response']['numFound'], 0)
