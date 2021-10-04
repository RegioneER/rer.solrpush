# -*- coding: utf-8 -*-
from operator import itemgetter
from plone import api
from plone.app.contentlisting.interfaces import IContentListing
from plone.app.querystring import queryparser
from plone.app.querystring.interfaces import IParsedQueryIndexModifier
from plone.app.querystring.interfaces import IQueryModifier
from plone.app.querystring.querybuilder import QueryBuilder as BaseView
from plone.batching import Batch
from Products.CMFCore.utils import getToolByName
from rer.solrpush.parser import SolrResponse
from rer.solrpush.utils.solr_indexer import get_site_title
from rer.solrpush.utils import search as solr_search
from zope.component import getUtilitiesFor


import logging


SORT_ON_MAPPING = {"sortable_title": "Title"}

logger = logging.getLogger(__name__)


class QueryBuilder(BaseView):
    def _makequery(
        self,
        query=None,
        batch=False,
        b_start=0,
        b_size=30,
        sort_on=None,
        sort_order=None,
        limit=0,
        brains=False,
        custom_query=None,
    ):
        """Parse the (form)query and return using multi-adapter"""
        query_modifiers = getUtilitiesFor(IQueryModifier)
        for name, modifier in sorted(query_modifiers, key=itemgetter(0)):
            query = modifier(query)

        parsedquery = queryparser.parseFormquery(
            self.context, query, sort_on, sort_order
        )
        index_modifiers = getUtilitiesFor(IParsedQueryIndexModifier)
        for name, modifier in index_modifiers:
            if name in parsedquery:
                new_name, query = modifier(parsedquery[name])
                parsedquery[name] = query
                # if a new index name has been returned, we need to replace
                # the native ones
                if name != new_name:
                    del parsedquery[name]
                    parsedquery[new_name] = query

        # Check for valid indexes
        catalog = getToolByName(self.context, "portal_catalog")
        valid_indexes = [
            index for index in parsedquery if index in catalog.indexes()
        ]

        # We'll ignore any invalid index, but will return an empty set if none
        # of the indexes are valid.
        if not valid_indexes:
            logger.warning(
                "Using empty query because there are no valid indexes used."
            )
            parsedquery = {}

        empty_query = not parsedquery  # store emptiness

        if batch:
            parsedquery["b_start"] = b_start
            parsedquery["b_size"] = b_size
        elif limit:
            parsedquery["sort_limit"] = limit

        if "path" not in parsedquery:
            parsedquery["path"] = {"query": ""}

        if isinstance(custom_query, dict) and custom_query:
            # Update the parsed query with an extra query dictionary. This may
            # override the parsed query. The custom_query is a dictonary of
            # index names and their associated query values.
            parsedquery.update(custom_query)
            empty_query = False

        # filter bad term and operator in query
        parsedquery = self.filter_query(parsedquery)
        results = []

        # RER.SOLRPUSH PATCH
        search_with_solr = False
        if "searchWithSolr" in parsedquery:
            if parsedquery["searchWithSolr"]["query"]:
                search_with_solr = True
            del parsedquery["searchWithSolr"]
        if not empty_query:
            if search_with_solr:
                if "SearchableText" in parsedquery:
                    if isinstance(parsedquery["SearchableText"], dict):
                        parsedquery["SearchableText"]["query"] = parsedquery[
                            "SearchableText"
                        ]["query"].rstrip("*")
                    else:
                        parsedquery["SearchableText"] = parsedquery[
                            "SearchableText"
                        ].rstrip("*")
                results = SolrResponse(
                    data=solr_search(
                        **self.clean_query_for_solr(query=parsedquery)
                    )
                )
            else:
                results = catalog(**parsedquery)
            if (
                getattr(results, "actual_result_count", False)
                and limit  # noqa
                and results.actual_result_count > limit  # noqa
            ):
                results.actual_result_count = limit

        if not brains and not search_with_solr:
            results = IContentListing(results)
        if batch:
            results = Batch(results, b_size, start=b_start)
        return results

    def clean_query_for_solr(self, query):
        fixed_query = {}
        filtered_sites = []
        for k, v in query.items():
            if k == "sort_on":
                fixed_query[k] = SORT_ON_MAPPING.get(v, v)
            elif k == "path":
                portal_state = api.content.get_view(
                    context=self.context,
                    request=self.request,
                    name=u"plone_portal_state",
                )
                root_path = portal_state.navigation_root_path()
                path = self.extract_value(v)
                if len(path) == 1 and path[0].rstrip("/") == root_path:
                    if "solr_sites" not in query.keys():
                        filtered_sites.append(get_site_title())
                else:
                    fixed_query["path_parents"] = path
            elif k == "solr_sites":
                sites = self.extract_value(v)
                if sites != "null":
                    filtered_sites = sites
            elif k == "solr_subjects":
                fixed_query["Subject"] = self.extract_value(v)
                continue
            elif k == "solr_portal_types":
                fixed_query["portal_type"] = self.extract_value(v)
                continue
            else:
                fixed_query[k] = v
            if filtered_sites:
                fixed_query["site_name"] = filtered_sites
        return {"query": fixed_query}

    def extract_value(self, value):
        if isinstance(value, dict) and "query" in value:
            return value["query"]
        return value
