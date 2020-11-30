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
from rer.solrpush.utils.solr_indexer import can_index
from rer.solrpush.utils.solr_indexer import create_index_dict
from rer.solrpush.utils import push_to_solr
from rer.solrpush.utils import remove_from_solr
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

    @property
    def index_fields(self):
        return api.portal.get_registry_record(
            "index_fields", interface=IRerSolrpushSettings, default=None
        )

    def index(self, obj, attributes=None):
        if (
            self.active
            and getattr(obj, "showinsearch", True)  # noqa
            and can_index(obj)  # noqa
        ):
            uid = obj.UID()
            data = create_index_dict(obj)
            self.queue = [item for item in self.queue if item[0] != uid] + [
                (uid, INDEX, data, attributes)
            ]
            return True
        return False

    def reindex(self, obj, attributes=None, update_metadata=None):
        if self.active:
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
                        default=u"There was a problem indexing or unindexing "
                        u"this content. Please take note of this address and "
                        u"contact site administrator.",
                    )
                    api.portal.show_message(
                        message=message, request=getRequest(), type="error"
                    )
            self.queue = []

    def abort(self):
        self.queue = []
