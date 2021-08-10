# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from plone import api
from plone.api.portal import set_registry_record
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.namedfile.file import NamedFile
from rer.solrpush.interfaces.settings import IRerSolrpushSettings
from rer.solrpush.utils import init_solr_push
from rer.solrpush.utils import reset_solr
from rer.solrpush.utils import search
from rer.solrpush.testing import RER_SOLRPUSH_API_FUNCTIONAL_TESTING
from transaction import commit

import unittest
import os


class TestTika(unittest.TestCase):
    """Test solr indexing for files"""

    layer = RER_SOLRPUSH_API_FUNCTIONAL_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        set_registry_record(
            "enabled_types", [u"File"], interface=IRerSolrpushSettings
        )
        init_solr_push()
        commit()

    def tearDown(self):
        set_registry_record("active", True, interface=IRerSolrpushSettings)
        reset_solr()
        commit()

    def create_file_item(self, filename):
        item_file = None
        with open(
            os.path.join(os.path.dirname(__file__), "docs", filename), "rb"
        ) as f:
            item_file = NamedFile(data=f.read(), filename=filename)

        file_item = api.content.create(
            container=self.portal, type="File", title=filename, file=item_file
        )
        commit()
        return file_item

    def test_index_and_extract_pdf(self):
        file_item = self.create_file_item(u"example.pdf")

        solr_results = search(query={"*": "*"}, fl="UID")
        self.assertEqual(solr_results.hits, 1)
        st_results = search(query={"SearchablesText": "lorem"}, fl="UID")
        self.assertEqual(st_results.hits, 1)
        self.assertEqual(file_item.UID(), st_results.docs[0]["UID"])

    def test_index_and_extract_docx(self):
        file_item = self.create_file_item(u"example.docx")

        solr_results = search(query={"*": "*"}, fl="UID SearchableText")
        self.assertEqual(solr_results.hits, 1)
        st_results = search(query={"SearchableText": "ipsum"}, fl="UID")
        self.assertEqual(st_results.hits, 1)
        self.assertEqual(file_item.UID(), st_results.docs[0]["UID"])

    def test_index_and_extract_ods(self):
        file_item = self.create_file_item(u"example.ods")

        solr_results = search(query={"*": "*"}, fl="UID SearchableText")
        self.assertEqual(solr_results.hits, 1)
        st_results = search(query={"SearchableText": "yyy"}, fl="UID")
        self.assertEqual(st_results.hits, 1)
        self.assertEqual(file_item.UID(), st_results.docs[0]["UID"])

    def test_indexed_file_has_right_mimetype(self):
        self.create_file_item(u"example.pdf")

        solr_results = search(query={"*": "*"}, fl="UID mime_type")
        self.assertEqual(solr_results.hits, 1)
        self.assertEqual(solr_results.docs[0]["mime_type"], "application/pdf")
