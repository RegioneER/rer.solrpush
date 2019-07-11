# -*- coding: utf-8 -*-
from plone import api
from rer.solrpush import logger
from rer.solrpush.interfaces import ISolrIndexQueueProcessor
from rer.solrpush.solr import push_to_solr
from zope.interface import implementer


INDEX = 1
UNINDEX = 2


# TODO: aggiungere un controllo sul browserlayer della request o togliere lo zcml
# e scommentare l'xml della componentregistry nei profiles

def checkbefore(f):
    def inner(self, *args, **kwargs):
        if self.active:
            if (f.__name__ in ('begin', 'commit', 'abort') or
                    args[0].portal_type in self.enabled_types):
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

    @checkbefore
    def index(self, obj, attributes=None):
        logger.debug('index %s, %s, %s', obj, attributes, self.queue)
        self.queue.append((INDEX, obj, attributes))

    @checkbefore
    def reindex(self, obj, attributes=None, update_metadata=None):
        logger.debug('reindex %s, %s, %s, %s', obj, attributes, update_metadata, self.queue)
        self.index(obj, attributes=attributes)

    @checkbefore
    def unindex(self, obj):
        logger.debug('unindex %s, %s', obj, self.queue)
        self.queue.append((UNINDEX, obj))

    @checkbefore
    def begin(self):
        logger.debug('begin %s', self.queue)
        self.queue = []

    @checkbefore
    def commit(self, wait=None):
        logger.debug('commit %s, %s', wait, self.queue)
        # TODO: è possibile con sol anche mandare un set di comandi (add+delete) in un
        #  unica volta, anzichè uno alla volta, valutare le due opzioni
        for action, obj, *args in self.queue:
            if action == INDEX:
                logger.info('solr index %s %s', obj, args)
                # TODO: valutare l'opzione di usare attributes (args[0]) per
                # indicizzare solo alcuni campi solr update
                push_to_solr(obj)
            elif action == UNINDEX:
                logger.warning('TODO solr unindex %s', obj)
        self.queue = []

    @checkbefore
    def abort(self):
        logger.debug('abort %s', self.queue)
        self.queue = []
