# -*- coding: utf-8 -*-
from plone import api
from plone.restapi.search.handler import SearchHandler
from plone.restapi.search.utils import unflatten_dotted_dict
from plone.restapi.services import Service
from rer.solrpush.interfaces.settings import IRerSolrpushSettings
from rer.solrpush.restapi.services.search.solr_search_handler import SolrSearchHandler


class SearchGet(Service):
    def reply(self):
        query = self.request.form.copy()
        query = unflatten_dotted_dict(query)
        active = api.portal.get_registry_record(
            "active", interface=IRerSolrpushSettings, default=False
        )
        search_with_solr = api.portal.get_registry_record(
            "search_with_solr", interface=IRerSolrpushSettings, default=False
        )
        if active and search_with_solr:
            return SolrSearchHandler(self.context, self.request).search(query)
        return SearchHandler(self.context, self.request).search(query)
