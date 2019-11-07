# -*- coding: utf-8 -*-
from plone import api
from rer.solrpush.interfaces import ISolrIndexQueueProcessor
from rer.solrpush.solr import push_to_solr
from rer.solrpush.solr import remove_from_solr
from zope.interface import implementer

import logging

logger = logging.getLogger(__name__)

INDEX = 1
UNINDEX = 2


# TODO: aggiungere un controllo sul browserlayer della request o togliere lo zcml
# e scommentare l'xml della componentregistry nei profiles (probabilmente la seconda
# è più pulita, testare però anche l'uninstall)

# TODO: il check su active e enabled_types in realtà potrebbe anche ssere fatto nei metodi
# index (push_to_solr) e unindex solr e tolto il decoratore


def checkbefore(f):
    def inner(self, *args, **kwargs):
        if self.active:
            if (
                f.__name__ in ('begin', 'commit', 'abort')
                or args[0].portal_type in self.enabled_types  # noqa
            ):
                return f(self, *args, **kwargs)
        logger.warning('skip solrpush for %s %s %s', f.__name__, args, kwargs)

    return inner


@implementer(ISolrIndexQueueProcessor)
class SolrIndexProcessor(object):
    queue = []

    @property
    def enabled_types(self):
        return api.portal.get_registry_record(
            'rer.solrpush.interfaces.IRerSolrpushSettings.enabled_types',
            default=False,
        )

    @property
    def active(self):
        return api.portal.get_registry_record(
            'rer.solrpush.interfaces.IRerSolrpushSettings.active',
            default=False,
        )

    def has_right_permission(self, obj):
        with api.env.adopt_roles(['Anonymous']):
            return api.user.has_permission('View', obj=obj)

    @checkbefore
    def index(self, obj, attributes=None):
        # logger.info('index %s, %s, %s', obj, attributes, self.queue)
        self.queue.append((INDEX, obj, attributes))

    @checkbefore
    def reindex(self, obj, attributes=None, update_metadata=None):
        # logger.info(
        #     'reindex %s, %s, %s, %s',
        #     obj,
        #     attributes,
        #     update_metadata,
        #     self.queue,
        # )
        if self.has_right_permission(obj):
            self.index(obj, attributes=attributes)
        else:
            self.unindex(obj)

    @checkbefore
    def unindex(self, obj):
        # logger.info('unindex %s, %s', obj, self.queue)
        self.queue.append((UNINDEX, obj, []))

    @checkbefore
    def begin(self):
        # logger.info('begin %s', self.queue)
        self.queue = []

    @checkbefore
    def commit(self, wait=None):
        # logger.info('commit %s, %s', wait, self.queue)
        # TODO: è possibile con sol anche mandare un set di comandi (add+delete) in un
        #  unica volta, anzichè uno alla volta, valutare le due opzioni
        for action, obj, args in self.queue:
            if action == INDEX:
                # logger.info('solr index %s %s', obj, args)
                # TODO: valutare l'opzione di usare attributes (args[0]) per
                # indicizzare solo alcuni campi solr update
                push_to_solr(obj)
            elif action == UNINDEX:
                remove_from_solr(obj.UID())
        self.queue = []

    @checkbefore
    def abort(self):
        logger.info('abort %s', self.queue)
        self.queue = []
