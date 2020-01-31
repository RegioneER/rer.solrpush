# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from plone import api
from plone.api.portal import set_registry_record
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.namedfile.file import NamedFile
from rer.solrpush.interfaces.settings import IRerSolrpushSettings
from rer.solrpush.solr import init_solr_push
from rer.solrpush.solr import reset_solr
from rer.solrpush.solr import search
from rer.solrpush.testing import RER_SOLRPUSH_FUNCTIONAL_TESTING
from transaction import commit

import unittest
import os


class TestTika(unittest.TestCase):
    """Test solr indexing for files"""

    layer = RER_SOLRPUSH_FUNCTIONAL_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        set_registry_record(
            'enabled_types', ['File'], interface=IRerSolrpushSettings
        )
        init_solr_push()

    def tearDown(self):
        set_registry_record('active', True, interface=IRerSolrpushSettings)
        reset_solr()

    def create_file_item(self, filename):
        file_item = api.content.create(
            container=self.portal, type='File', title=filename
        )
        with open(
            os.path.join(os.path.dirname(__file__), 'docs', filename), 'rb'
        ) as f:
            file_item.file = NamedFile(data=f.read(), filename=filename)
        return file_item

    def test_index_and_extract_pdf(self):
        file_item = self.create_file_item(u'example.pdf')
        commit()
        solr_results = search(query={'*': '*'}, fl='UID')
        self.assertEqual(solr_results.hits, 1)
        st_results = search(query={'SearchablesText': 'lorem'}, fl='UID')
        self.assertEqual(st_results.hits, 1)
        self.assertEqual(file_item.UID(), st_results.docs[0]['UID'])

    def test_index_and_extract_docx(self):
        file_item = self.create_file_item(u'example.docx')
        commit()
        solr_results = search(query={'*': '*'}, fl='UID SearchableText')
        self.assertEqual(solr_results.hits, 1)
        st_results = search(query={'SearchableText': 'ipsum'}, fl='UID')
        self.assertEqual(st_results.hits, 1)
        self.assertEqual(file_item.UID(), st_results.docs[0]['UID'])

    def test_index_and_extract_ods(self):
        file_item = self.create_file_item(u'example.ods')
        commit()
        solr_results = search(query={'*': '*'}, fl='UID SearchableText')
        self.assertEqual(solr_results.hits, 1)
        st_results = search(query={'SearchableText': 'yyy'}, fl='UID')
        self.assertEqual(st_results.hits, 1)
        self.assertEqual(file_item.UID(), st_results.docs[0]['UID'])
