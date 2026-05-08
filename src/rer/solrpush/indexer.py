# -*- coding: utf-8 -*-
# from operator import itemgetter
from plone import api
from Products.CMFCore.indexing import INDEX
from Products.CMFCore.indexing import REINDEX
from Products.CMFCore.indexing import UNINDEX
from pysolr import SolrError
from rer.solrpush import _
from rer.solrpush.interfaces import IRerSolrpushLayer
from rer.solrpush.interfaces import ISolrIndexQueueProcessor
from rer.solrpush.interfaces.settings import IRerSolrpushSettings
from rer.solrpush.utils import push_to_solr
from rer.solrpush.utils import remove_from_solr
from rer.solrpush.utils.solr_indexer import can_index
from rer.solrpush.utils.solr_indexer import create_index_dict
from zope.globalrequest import getRequest
from zope.interface import implementer

import logging

logger = logging.getLogger(__name__)


@implementer(ISolrIndexQueueProcessor)
class SolrIndexProcessor(object):
    queue = []

    @property
    def active(self):
        return IRerSolrpushLayer.providedBy(
            getRequest()
        ) and api.portal.get_registry_record(
            "active", interface=IRerSolrpushSettings, default=False
        )

    @property
    def enabled_types(self):
        return api.portal.get_registry_record(
            "enabled_types", interface=IRerSolrpushSettings, default=[]
        )

    def index(self, obj, attributes=None):
        if (
            self.active
            and self.check_attributes(attributes=attributes)  # noqa
            and can_index(obj)  # noqa
        ):
            uid = obj.UID()
            with api.env.adopt_roles(["Anonymous"]):
                data = create_index_dict(obj)
            self.queue = [item for item in self.queue if item[0] != uid] + [
                (uid, INDEX, data, attributes)
            ]
            return True
        return False

    def check_attributes(self, attributes):
        """
        If we are reindexing a subset of indexes that are not sent to SOLR,
        skip the update.
        """
        if not attributes:
            return True
        catalog = api.portal.get_tool(name="portal_catalog")
        catalog_indexes = set(catalog.indexes())
        return any(attr in catalog_indexes for attr in attributes)

    def reindex(self, obj, attributes=None, update_metadata=None):
        if self.active and self.check_attributes(attributes=attributes):
            if not self.index(obj, attributes):
                self.unindex(obj)

    def unindex(self, obj):
        if self.active:
            uid = obj.UID()
            self.queue = [item for item in self.queue if item[0] != uid] + [
                (uid, UNINDEX, None, None)
            ]

    def begin(self):
        pass

    def commit(self, wait=None):
        if self.active and self.queue:
            # TODO: è possibile con sol anche mandare un set di comandi (add+delete) in un
            #  unica volta, anzichè uno alla volta, valutare le due opzioni
            # Sort so unindex operations come first
            # for iop, obj in sorted(res.values(), key=itemgetter(0)):
            for uid, iop, data, args in self.queue:
                try:
                    if iop in (INDEX, REINDEX):
                        push_to_solr(data)
                    elif iop == UNINDEX:
                        remove_from_solr(uid)
                except SolrError:
                    logger.exception("error indexing %s %s", iop, uid)
                    message = _(
                        "content_indexed_error",
                        default="There was a problem indexing or unindexing "
                        "this content. Please take note of this address and "
                        "contact site administrator.",
                    )
                    api.portal.show_message(
                        message=message, request=getRequest(), type="warning"
                    )
            self.queue = []

    def abort(self):
        self.queue = []
