# -*- coding: utf-8 -*-
from rer.solrpush.utils import search
from rer.solrpush.utils.solr_search import SOLRException
from zope.interface import implementer
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

import logging


logger = logging.getLogger(__name__)


class FacetsVocabulary(object):
    facet_field = ""

    def get_terms(self):
        try:
            solr_results = search(
                query={"*": "*", "b_size": 1},
                fl="UID",
                facets=True,
                facet_fields=self.facet_field,
            )
        except SOLRException:
            logger.exception("")
            return []
        if isinstance(solr_results, dict) and solr_results.get("error", False):
            return []
        facets = solr_results.facets["facet_fields"].get(self.facet_field, [])
        if not facets:
            return []
        terms = []
        for facet in facets:
            for key in facet.keys():
                terms.append(
                    SimpleTerm(value=key, token=key.encode("utf-8"), title=key)
                )
        return sorted(terms, key=lambda x: x.title.lower())

    def __call__(self, context):
        return SimpleVocabulary(self.get_terms(), swallow_duplicates=True)


@implementer(IVocabularyFactory)
class AvailableSitesVocabularyFactory(FacetsVocabulary):
    facet_field = "site_name"


@implementer(IVocabularyFactory)
class AvailableSubjectsVocabularyFactory(FacetsVocabulary):
    facet_field = "Subject"


@implementer(IVocabularyFactory)
class AvailablePortalTypesVocabularyFactory(FacetsVocabulary):
    facet_field = "portal_type"


AvailablePortalTypesVocabulary = AvailablePortalTypesVocabularyFactory()
AvailableSitesVocabulary = AvailableSitesVocabularyFactory()
AvailableSubjectsVocabulary = AvailableSubjectsVocabularyFactory()
