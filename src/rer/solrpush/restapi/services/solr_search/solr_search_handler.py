# -*- coding: utf-8 -*-
from copy import deepcopy
from plone.restapi.deserializer import boolean_value
from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.search.handler import SearchHandler as BaseHandler
from plone.restapi.serializer.summary import merge_serializer_metadata_utilities_data
from Products.CMFCore.utils import getToolByName
from rer.solrpush.parser import SolrResponse
from rer.solrpush.utils import search as solr_search
from zope.component import getMultiAdapter


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
        facets = boolean_value(solr_query.get("facets", False))
        facet_fields = solr_query.get("facet_fields", [])
        query_params = {}
        if facets:
            query_params["facets"] = facets
            if facet_fields:
                query_params["facet_fields"] = facet_fields
                del solr_query["facet_fields"]
            if "facets" in solr_query:
                del solr_query["facets"]
        query_params["query"] = solr_query
        return self.serialize_results(solr_search(**query_params))

    def metadata_fields(self, query):
        metadata = merge_serializer_metadata_utilities_data()
        default_metadata_fields = metadata["default_metadata_fields"]
        additional_metadata_fields = query.get("metadata_fields", [])
        if not isinstance(additional_metadata_fields, list):
            additional_metadata_fields = [additional_metadata_fields]
        additional_metadata_fields = set(additional_metadata_fields)
        if additional_metadata_fields:
            del query["metadata_fields"]
        return default_metadata_fields | additional_metadata_fields

    def serialize_results(self, solr_results):
        results = getMultiAdapter(
            (SolrResponse(data=solr_results), self.request), ISerializeToJson
        )()
        if solr_results.facets:
            results["facets"] = solr_results.facets.get("facet_fields", {})
        return results
