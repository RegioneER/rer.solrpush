# -*- coding: utf-8 -*-
from rer.solrpush.utils import search
from zope.interface import implementer
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm


@implementer(IVocabularyFactory)
class AvailableSitesVocabularyFactory(object):
    @property
    def terms(self):
        solr_results = search(
            query={"*": "*", "b_size": 1},
            fl="UID",
            facets=True,
            facet_fields="site_name",
        )
        if isinstance(solr_results, dict) and solr_results.get("error", False):
            return []
        facets = solr_results.facets["facet_fields"].get("site_name", [])
        if not facets:
            return []
        terms = []
        for facet in facets:
            for key in facet.keys():
                terms.append(
                    SimpleTerm(value=key, token=key.encode("utf-8"), title=key)
                )
        return terms

    def __call__(self, context):
        return SimpleVocabulary(self.terms)


@implementer(IVocabularyFactory)
class AvailableSubjectsVocabularyFactory(object):
    @property
    def terms(self):
        solr_results = search(
            query={"*": "*", "b_size": 1},
            fl="UID",
            facets=True,
            facet_fields="Subject",
        )
        if isinstance(solr_results, dict) and solr_results.get("error", False):
            return []
        facets = solr_results.facets["facet_fields"].get("Subject", [])
        if not facets:
            return []
        terms = []
        for facet in facets:
            for key in facet.keys():
                terms.append(
                    SimpleTerm(value=key, token=key.encode("utf-8"), title=key)
                )
        return terms

    def __call__(self, context):
        # we use swallow_duplicates to avoid errors.
        # SimpleVocabulary init in zope.schema 4.5.0 strips "strange" chars
        # In python3 probably this is unnecessary
        return SimpleVocabulary(terms=self.terms, swallow_duplicates=True)


AvailableSitesVocabulary = AvailableSitesVocabularyFactory()
AvailableSubjectsVocabulary = AvailableSubjectsVocabularyFactory()
