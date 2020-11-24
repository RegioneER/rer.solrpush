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
            query={"*": "*"}, fl="UID", facets=True, facet_fields="site_name"
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


AvailableSitesVocabulary = AvailableSitesVocabularyFactory()
