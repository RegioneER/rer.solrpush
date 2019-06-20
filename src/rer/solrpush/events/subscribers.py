# -*- coding: utf-8 -*-
from rer.solrpush.data_manager import SolrPushDataManager

import logging
import transaction


logger = logging.getLogger(__name__)


def pushToSolr(item):
    manager = SolrPushDataManager(item=item)
    transaction.get().join(manager)


def objectAdded(item, ev):
    logger.info(ev)
    pushToSolr(item)


def objectModified(item, ev):
    logger.info(ev)
    pushToSolr(item)


def objectCopied(item, ev):
    logger.info(ev)
    pushToSolr(item)


def objectRemoved(item, ev):
    logger.info(ev)
    pushToSolr(item)


def objectMoved(item, ev):
    logger.info(ev)
    pushToSolr(item)


def dispatchObjectMovedEvent(item, ev):
    logger.info(ev)
    pushToSolr(item)


def objectTransitioned(item, ev):
    logger.info(ev)
    pushToSolr(item)
