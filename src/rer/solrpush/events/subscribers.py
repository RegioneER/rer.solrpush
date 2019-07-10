# -*- coding: utf-8 -*-
from plone import api
from rer.solrpush.data_manager import SolrPushDataManager


import logging
import transaction


logger = logging.getLogger(__name__)


def pushToSolr(item, ev):
    """
    Checks before the real push

    Se non sono specificati gli enabled_types, allora mettiamo il manager
    a tutti.
    """

    enabled_types = api.portal.get_registry_record(
        'rer.solrpush.interfaces.IRerSolrpushSettings.enabled_types',
        default=False,
    )

    active = api.portal.get_registry_record(
        'rer.solrpush.interfaces.IRerSolrpushSettings.active',
        default=False,
    )

    # Don't add the manager if we don't have to index this type of item.
    if not active:
        return

    if enabled_types and item.portal_type not in enabled_types:
        return

    manager = SolrPushDataManager(item=item)
    transaction.get().join(manager)


# def objectAdded(item, ev):
#     logger.info("objectAdded")
#     pushToSolr(item)
#
#
# def objectModified(item, ev):
#     logger.info("objectModified")
#     pushToSolr(item)
#
#
# def objectCopied(item, ev):
#     logger.info("objectCopied")
#     pushToSolr(item)
#
#
# def objectRemoved(item, ev):
#     logger.info("objectRemoved")
#     pushToSolr(item)
#
#
# def objectMoved(item, ev):
#     logger.info("objectMoved")
#     pushToSolr(item)
#
#
# def dispatchObjectMovedEvent(item, ev):
#     logger.info("dispatchObjectMovedEvent")
#     pushToSolr(item)
#
#
# def objectTransitioned(item, ev):
#     logger.info("objectTransitioned")
#     pushToSolr(item)
