# -*- coding: utf-8 -*-
from operator import itemgetter
from plone import api
from pysolr import SolrError
from rer.solrpush import _
from rer.solrpush.interfaces import IRerSolrpushLayer
from rer.solrpush.interfaces import ISolrIndexQueueProcessor
from rer.solrpush.interfaces.settings import IRerSolrpushSettings
from rer.solrpush.solr import push_to_solr
from rer.solrpush.solr import remove_from_solr
from zope.globalrequest import getRequest
from zope.interface import implementer

import logging


logger = logging.getLogger(__name__)

UNINDEX = -1
REINDEX = 0
INDEX = 1


@implementer(ISolrIndexQueueProcessor)
class SolrIndexProcessor(object):
    queue = []

    @property
    def active(self):
        return IRerSolrpushLayer.providedBy(
            getRequest()
        ) and api.portal.get_registry_record(
            "active", interface=IRerSolrpushSettings, default=""
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

    def has_right_permission(self, obj):
        with api.env.adopt_roles(["Anonymous"]):
            return api.user.has_permission("View", obj=obj)

    def index(self, obj, attributes=None):
        if self.active and getattr(obj, "showinsearch", True):
            self.queue.append((INDEX, obj, attributes))

    def reindex(self, obj, attributes=None, update_metadata=None):
        """
        Here we check only if the object has the right state
        """
        if self.active:
            if self.has_right_permission(obj) and getattr(
                obj, "showinsearch", True
            ):
                self.index(obj, attributes=attributes)
            else:
                self.unindex(obj)

    def unindex(self, obj):
        if self.active:
            self.queue.append((UNINDEX, obj, []))

    def begin(self):
        pass
        # self.queue = []

    def commit(self, wait=None):
        if self.active and self.queue:
            # optimize queue (args are ignored)
            res = {}
            for iop, obj, args in self.queue:
                hash_id = hash(obj)
                # func = getattr(obj, 'getPhysicalPath', None)
                # if callable(func):
                #     hash_id = hash_id, func()
                op, dummy = res.get(hash_id, (0, obj))
                # If we are going to delete an item that was added in this
                # transaction, ignore it
                if op == INDEX and iop == UNINDEX:
                    del res[hash_id]
                else:
                    if op == UNINDEX and iop == REINDEX:
                        op = REINDEX
                    else:
                        # Operators are -1, 0 or 1 which makes it safe to add them
                        op += iop
                        # operator always within -1 and 1
                        op = min(max(op, UNINDEX), INDEX)
                    res[hash_id] = (op, obj)

            # print('finished reducing; %s -> %s item(s) in queue...', self.queue, res)
            # print('finished reducing; %d -> %d item(s) in queue...', len(self.queue), len(res))

            # TODO: è possibile con sol anche mandare un set di comandi (add+delete) in un
            #  unica volta, anzichè uno alla volta, valutare le due opzioni
            # Sort so unindex operations come first
            for iop, obj in sorted(res.values(), key=itemgetter(0)):
                try:
                    if iop in (INDEX, REINDEX):
                        push_to_solr(obj)
                    elif iop == UNINDEX:
                        remove_from_solr(obj.UID())
                except SolrError:
                    logger.exception("error indexing %s", obj.UID())
                    message = _(
                        "content_indexed_error",
                        default=u"There was a problem indexing this content. Please "
                        "contact site administrator.",
                    )
                    api.portal.show_message(
                        message=message, request=obj.REQUEST, type="error"
                    )
            self.queue = []

    def abort(self):
        self.queue = []
