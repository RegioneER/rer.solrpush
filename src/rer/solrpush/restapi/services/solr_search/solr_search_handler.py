# -*- coding: utf-8 -*-
from copy import deepcopy
from Products.CMFCore.utils import getToolByName
from plone.restapi.search.handler import SearchHandler as BaseHandler
from rer.solrpush.utils import search as solr_search
from rer.solrpush.restapi.services.solr_search.batch import SolrHypermediaBatch
from plone.restapi.deserializer import boolean_value

DEFAULT_METADATA_FIELDS = set(
    ["@id", "@type", "description", "review_state", "title"]
)
FIELD_ACCESSORS = {
    "@id": "getURL",
    "@type": "PortalType",
    "description": "Description",
    "title": "Title",
}

NON_METADATA_ATTRIBUTES = set(["getPath", "getURL"])

BLACKLISTED_ATTRIBUTES = set(["getDataOrigin", "getObject", "getUserData"])


class SolrSearchHandler(BaseHandler):
    """Executes a solr search based on a query dict, and returns
    JSON compatible results.
    """

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.catalog = getToolByName(self.context, "portal_catalog")

    def search(self, query=None):
        if query is None:
            solr_query = {}
        else:
            solr_query = deepcopy(query)
        fl = self.get_fields_list(solr_query)
        facets = boolean_value(solr_query.get("facets", False))
        facet_fields = solr_query.get("facet_fields", [])
        query_params = {"fl": fl}
        if facets:
            query_params["facets"] = facets
            if facet_fields:
                query_params["facet_fields"] = facet_fields
                del solr_query["facet_fields"]
            if "facets" in solr_query:
                del solr_query["facets"]
        query_params["query"] = solr_query
        return self.serialize_results(solr_search(**query_params))

    def get_fields_list(self, query):
        if "fullobjects" in query:
            del query["fullobjects"]
            return []
        fields = []
        for field in self.metadata_fields(query):
            if field.startswith("_") or field in BLACKLISTED_ATTRIBUTES:
                continue
            fields.append(field)
        return fields

    def metadata_fields(self, query):
        additional_metadata_fields = query.get("metadata_fields", [])
        if not isinstance(additional_metadata_fields, list):
            additional_metadata_fields = [additional_metadata_fields]
        additional_metadata_fields = set(additional_metadata_fields)
        if additional_metadata_fields:
            del query["metadata_fields"]
        return DEFAULT_METADATA_FIELDS | additional_metadata_fields

    def serialize_results(self, solr_results):
        batch = SolrHypermediaBatch(self.request, solr_results)
        results = {}
        results["@id"] = batch.canonical_url
        results["items_total"] = solr_results.hits
        if solr_results.facets:
            results["facets"] = solr_results.facets.get("facet_fields", {})
        links = batch.links
        if links:
            results["batching"] = links

        results["items"] = solr_results.docs

        return results
