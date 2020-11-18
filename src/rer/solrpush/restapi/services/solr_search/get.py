# -*- coding: utf-8 -*-
from plone.restapi.search.utils import unflatten_dotted_dict
from plone.restapi.services import Service
from rer.solrpush.restapi.services.solr_search.solr_search_handler import (
    SolrSearchHandler,
)


class SearchGet(Service):
    def reply(self):
        query = self.request.form.copy()
        query = unflatten_dotted_dict(query)
        return SolrSearchHandler(self.context, self.request).search(query)
