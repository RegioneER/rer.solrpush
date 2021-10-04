# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from rer.solrpush.utils.solr_common import init_solr_push
from rer.solrpush.utils.solr_common import get_solr_connection
from rer.solrpush.utils import push_to_solr
from rer.solrpush.testing import RER_SOLRPUSH_API_FUNCTIONAL_TESTING
from transaction import commit
from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory

import unittest


class TestVocabularies(unittest.TestCase):
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

        init_solr_push()
        commit()

        push_to_solr(
            {
                "title": "Document from site foo",
                "portal_type": "Document",
                "site_name": "foo",
                "UID": "000",
            }
        )
        push_to_solr(
            {
                "title": "Document from site foo with subject",
                "portal_type": "Document",
                "site_name": "foo",
                "Subject": ["foo-subject"],
                "UID": "111",
            }
        )
        push_to_solr(
            {
                "title": "Document from site bar",
                "portal_type": "Document",
                "site_name": "bar",
                "UID": "222",
            }
        )
        push_to_solr(
            {
                "title": "News Item from site bar",
                "portal_type": "News Item",
                "site_name": "bar",
                "Subject": ["bar-subject"],
                "UID": "333",
            }
        )

    def tearDown(self):
        solr = get_solr_connection()
        solr.delete(q="*:*", commit=True)
        commit()

    def test_sites_vocabulary_return_all_stored_ones(self):
        factory = getUtility(
            IVocabularyFactory, "rer.solrpush.vocabularies.AvailableSites"
        )
        vocabulary = factory(self.portal)

        self.assertEqual(len(vocabulary), 2)
        self.assertEqual([x.title for x in vocabulary], ["bar", "foo"])
        self.assertEqual(vocabulary.getTerm("foo").title, "foo")
        self.assertEqual(vocabulary.getTerm("bar").title, "bar")

    def test_Subject_vocabulary_return_all_stored_ones(self):
        factory = getUtility(
            IVocabularyFactory, "rer.solrpush.vocabularies.AvailableSubjects"
        )
        vocabulary = factory(self.portal)

        self.assertEqual(len(vocabulary), 2)
        self.assertEqual(
            [x.title for x in vocabulary], ["bar-subject", "foo-subject"]
        )
        self.assertEqual(
            vocabulary.getTerm("foo-subject").title, "foo-subject"
        )
        self.assertEqual(
            vocabulary.getTerm("bar-subject").title, "bar-subject"
        )

    def test_portal_type_vocabulary_return_all_stored_ones(self):
        factory = getUtility(
            IVocabularyFactory,
            "rer.solrpush.vocabularies.AvailablePortalTypes",
        )
        vocabulary = factory(self.portal)

        self.assertEqual(len(vocabulary), 2)
        self.assertEqual(
            [x.title for x in vocabulary], ["Document", "News Item"]
        )
        self.assertEqual(vocabulary.getTerm("Document").title, "Document")
        self.assertEqual(vocabulary.getTerm("News Item").title, "News Item")
