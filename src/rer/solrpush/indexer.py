# -*- coding: utf-8 -*-
# from operator import itemgetter
from plone import api
from plone.dexterity.interfaces import IDexterityContent
from plone.indexer import indexer
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
from six.moves import range
from zope.globalrequest import getRequest
from zope.interface import implementer

import json
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
        indexes = api.portal.get_registry_record(
            "index_fields", interface=IRerSolrpushSettings, default="{}"
        )
        if not indexes:
            return {}
        return json.loads(indexes)

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
        If we are reindexing some indexes that should not be indexed on SOLR,
        we don't have to update it.
        """
        if not attributes:
            return True
        index_fields = api.portal.get_registry_record(
            "index_fields", interface=IRerSolrpushSettings, default="{}"
        )
        if not index_fields:
            return False
        index_fields = json.loads(index_fields)

        found = False
        for index in attributes:
            if index in index_fields:
                found = True
        return found

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


@indexer(IDexterityContent)
def path_depth(obj, **kwargs):
    """return depth of physical path"""
    return len(obj.getPhysicalPath())


@indexer(IDexterityContent)
def path_parents(obj, **kwargs):
    """return all parent paths leading up to the object"""
    elements = obj.getPhysicalPath()
    return ["/".join(elements[: n + 1]) for n in range(1, len(elements))]
