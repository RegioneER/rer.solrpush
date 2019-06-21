# -*- coding: utf-8 -*-
from plone import api
from rer.solrpush.data_manager import SolrPushDataManager

import logging
import transaction


logger = logging.getLogger(__name__)


def pushToSolr(item):
    """
    Checks before the real push
    """
    manager = SolrPushDataManager(item=item)

    enabled_types = api.portal.get_registry_record(
        'rer.solrpush.interfaces.IRerSolrpushSettings.enabled_types'
    )

    if item.portal_type in enabled_types:
        transaction.get().join(manager)


def objectAdded(item, ev):
    logger.info("objectAdded")
    logger.info(ev)
    pushToSolr(item)


def objectModified(item, ev):
    logger.info("objectModified")
    logger.info(ev)
    pushToSolr(item)


def objectCopied(item, ev):
    logger.info("objectCopied")
    logger.info(ev)
    pushToSolr(item)


def objectRemoved(item, ev):
    logger.info("objectRemoved")
    logger.info(ev)
    pushToSolr(item)


def objectMoved(item, ev):
    logger.info("objectMoved")
    logger.info(ev)
    pushToSolr(item)


def dispatchObjectMovedEvent(item, ev):
    logger.info("dispatchObjectMovedEvent")
    logger.info(ev)
    pushToSolr(item)


def objectTransitioned(item, ev):
    logger.info("objectTransitioned")
    logger.info(ev)
    pushToSolr(item)
