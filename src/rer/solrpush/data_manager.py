# -*- coding: utf-8 -*-
from rer.solrpush.solr import push_to_solr
from transaction.interfaces import IDataManager
from transaction.interfaces import ISavepoint
from zope.interface import implementer

import logging

# import transaction

logger = logging.getLogger(__name__)


@implementer(ISavepoint)
class DummySavepoint:

    valid = property(lambda self: self.transaction is not None)

    def __init__(self, datamanager):
        self.datamanager = datamanager

    def rollback(self):
        pass


@implementer(IDataManager)
# @adapter(IDexterityItem)
class SolrPushDataManager(object):
    def __init__(self, item):
        self.item = item

    def onAbort(self):
        pass

    def commit(self, txn):
        pass

    def abort(self, txn):
        self.onAbort()

    def sortKey(self):
        return self.item.UID()

    # # No subtransaction support.
    def abort_sub(self, txn):
        pass

    #     "This object does not do anything with subtransactions"

    commit_sub = abort_sub

    def beforeCompletion(self, txn):
        pass

    #     "This object does not do anything in beforeCompletion"

    afterCompletion = beforeCompletion

    def tpc_begin(self, txn, subtransaction=False):
        assert not subtransaction

    def tpc_vote(self, txn):
        pass

    #     if self.vote is not None:
    #         return self.vote(*self.args)

    def tpc_finish(self, txn):
        push_to_solr(self.item)

    tpc_abort = abort

    def savepoint(self):
        return DummySavepoint(self)


# class SolrPushTransactionManager(object):
#     def pushToSolr(self, item):
#         datamanager = SolrPushDataManager(item=item)
#         transaction.get().join(datamanager)
