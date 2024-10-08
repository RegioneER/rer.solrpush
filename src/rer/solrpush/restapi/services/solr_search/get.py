# -*- coding: utf-8 -*-
from plone import api
from plone.restapi.search.handler import SearchHandler
from plone.restapi.search.utils import unflatten_dotted_dict
from plone.restapi.services import Service
from rer.solrpush.interfaces.settings import IRerSolrpushSettings
from rer.solrpush.restapi.services.solr_search.solr_search_handler import (
    SolrSearchHandler,
)


class SearchGet(Service):
    def reply(self):
        query = self.request.form.copy()
        query = unflatten_dotted_dict(query)
        handler = SearchHandler
        try:
            search_enabled = api.portal.get_registry_record(
                "search_enabled", interface=IRerSolrpushSettings
            )
        except Exception:
            return handler(self.context, self.request).search(query)
        if search_enabled:
            handler = SolrSearchHandler
        return handler(self.context, self.request).search(query)
