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

import requests
import unittest

try:
    from Products.CMFPlone.utils import get_installer
except ImportError:
    get_installer = None


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

    def test_item_not_indexed_if_solrpus_is_not_ready(self):
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
