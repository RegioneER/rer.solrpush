# -*- coding: utf-8 -*-
from plone import api
from pysolr import SolrError
from rer.solrpush import _
from rer.solrpush.interfaces import ISolrIndexQueueProcessor
from rer.solrpush.interfaces.settings import IRerSolrpushSettings
from rer.solrpush.solr import push_to_solr
from rer.solrpush.solr import remove_from_solr
from zope.interface import implementer

import logging

logger = logging.getLogger(__name__)

INDEX = 1
UNINDEX = 2


@implementer(ISolrIndexQueueProcessor)
class SolrIndexProcessor(object):
    queue = []

    @property
    def active(self):
        return api.portal.get_registry_record(
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
        if getattr(obj, "showinsearch", True):
            self.queue.append((INDEX, obj, attributes))

    def reindex(self, obj, attributes=None, update_metadata=None):
        """
        Here we check only if the object has the right state
        """
        if self.has_right_permission(obj) and getattr(obj, "showinsearch", True):
            self.index(obj, attributes=attributes)
        else:
            self.unindex(obj)
        return

    def unindex(self, obj):
        self.queue.append((UNINDEX, obj, []))

    def begin(self):
        pass
        # self.queue = []

    def commit(self, wait=None):
        # TODO: è possibile con sol anche mandare un set di comandi (add+delete) in un
        #  unica volta, anzichè uno alla volta, valutare le due opzioni
        for action, obj, args in self.queue:
            try:
                if action == INDEX:
                    push_to_solr(obj)
                elif action == UNINDEX:
                    remove_from_solr(obj.UID())
            except SolrError as err:
                logger.exception(err)
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
