# -*- coding: utf-8 -*-
from plone import api
from rer.solrpush.data_manager import SolrRemoveDataManager
from rer.solrpush.data_manager import SolrPushDataManager
from zope.lifecycleevent import ObjectRemovedEvent

import logging
import transaction


logger = logging.getLogger(__name__)


def can_index(item):
    enabled_types = api.portal.get_registry_record(
        'rer.solrpush.interfaces.IRerSolrpushSettings.enabled_types',
        default=False,
    )

    active = api.portal.get_registry_record(
        'rer.solrpush.interfaces.IRerSolrpushSettings.active', default=False
    )
    # Don't add the manager if we don't have to index this type of item.
    if not active:
        return False
    if enabled_types and item.portal_type not in enabled_types:
        return False
    return True


def pushToSolr(item, ev):
    """
    Checks before the real push

    Se non sono specificati gli enabled_types, allora mettiamo il manager
    a tutti.
    """
    if isinstance(ev, ObjectRemovedEvent):
        # ObjectRemovedEvent implements also ObjectModifiedEvent, so this means
        # that ObjectModifiedEvent will be fired also when we are deletin
        # an item.
        return
    # logger.info('EVENTO: {}'.format(ev))
    if can_index(item):
        manager = SolrPushDataManager(item=item)
        transaction.get().join(manager)


def objectRemoved(item, ev):
    if can_index(item):
        manager = SolrRemoveDataManager(item=item)
        transaction.get().join(manager)
