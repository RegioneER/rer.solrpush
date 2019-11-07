# -*- coding: utf-8 -*-
from AccessControl import Unauthorized
from persistent.dict import PersistentDict
from plone import api
from plone.protect.authenticator import createToken
from Products.CMFCore.interfaces import IIndexQueueProcessor
from Products.Five import BrowserView
from rer.solrpush import _
from rer.solrpush.solr import reset_solr
from time import strftime
from time import time
from transaction import commit
from z3c.form import button
from z3c.form import form
from zope.annotation.interfaces import IAnnotations
from zope.component import getMultiAdapter
from zope.component import getSiteManager

import logging
import json

logger = logging.getLogger(__name__)


def timer(func=time):
    """ set up a generator returning the elapsed time since the last call """

    def gen(last=func()):
        while True:
            elapsed = func() - last
            last = func()
            yield "%.3fs" % elapsed

    return gen()


class SolrMaintenanceBaseForm(form.Form):

    # template = ViewPageTemplateFile('templates/reindex_solr.pt')

    ignoreContext = True

    @button.buttonAndHandler(_('start_label', default=u'Start'))
    def handleApply(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        self.do_action()


class ResetSolr(SolrMaintenanceBaseForm):
    """
    Reset solr index
    """

    label = _('maintenance_reset_solr_label', default="Reset SOLR index")
    description = _(
        'maintenance_reset_solr_description',
        default="Drop all items in SOLR index.",
    )

    def do_action(self):
        reset_solr()
        msg_label = _(
            'maintenance_reset_success', default='SOLR index dropped'
        )
        logger.info('##### SOLR Index dropped #####')
        api.portal.show_message(message=msg_label, request=self.request)


class SyncSolr(SolrMaintenanceBaseForm):

    label = _('maintenance_sync_solr_label', default="Sync SOLR index")
    description = _(
        'maintenance_sync_solr_description',
        default='Remove no longer existing contents from SOLR and index'
        ' missing objects.',
    )

    def do_action(self):

        msg_label = _(
            'maintenance_reset_success', default='SOLR index dropped'
        )
        logger.info('##### SOLR Index dropped')
        self.status = msg_label


class ReindexBaseView(BrowserView):
    def reindexPloneToSolr(self):
        annotations = IAnnotations(api.portal.get())
        sm = getSiteManager()
        utility = sm.queryUtility(IIndexQueueProcessor, name="solrpush")
        if not utility:
            self.status = self.formErrorsMessage
            return
        elapsed = timer()
        utility.begin()
        brains = api.content.find(portal_type=utility.enabled_types)
        annotations['solr_reindex'] = PersistentDict(
            {
                'in_progress': True,
                'tot': brains.actual_result_count,
                'counter': 0,
                'timestamp': strftime("%Y/%m/%d-%H:%M:%S "),
                'message': 'Reindex items on SOLR',
            }
        )
        commit()
        status = annotations['solr_reindex']
        logger.info('##### SOLR REINDEX START #####')
        logger.info('Reindexing {} items.'.format(brains.actual_result_count))
        for i, brain in enumerate(brains):
            status['counter'] = status['counter'] + 1
            commit()
            obj = brain.getObject()
            utility.reindex(obj, [])
            logger.info(
                '[{index}/{total}] {path} ({type})'.format(
                    index=i + 1,
                    total=brains.actual_result_count,
                    path=brain.getPath(),
                    type=brain.portal_type,
                )
            )

            utility.commit()
        status['in_progress'] = False
        elapsed_time = next(elapsed)
        logger.info('SOLR Reindex completed in {}'.format(elapsed_time))

    def cleanupSolrIndex(self):
        pass
        # annotations = IAnnotations(api.portal.get())
        # sm = getSiteManager()
        # elapsed = timer()
        # pc = api.portal.get_tool(name='portal_catalog')
        # uids = pc.uniqueValuesFor('UID')
        # solr_result = search({'*': '*'})
        # import pdb

        # pdb.set_trace()
        # annotations['solr_reindex'] = PersistentDict(
        #     {
        #         'in_progress': True,
        #         'tot': brains.actual_result_count,
        #         'counter': 0,
        #         'timestamp': strftime("%Y/%m/%d-%H:%M:%S "),
        #         'message': 'Reindex items on SOLR',
        #     }
        # )
        # status = annotations['solr_reindex']
        # logger.info('##### SOLR REINDEX START #####')
        # logger.info('Reindexing {} items.'.format(brains.actual_result_count))
        # # TODO
        # status['in_progress'] = False
        # elapsed_time = next(elapsed)
        # logger.info('SOLR Reindex completed in {}'.format(elapsed_time))


class DoReindexView(ReindexBaseView):
    def __call__(self):
        authenticator = getMultiAdapter(
            (self.context, self.request), name=u"authenticator"
        )
        if not authenticator.verify():
            raise Unauthorized
        self.reindexPloneToSolr()


class DoSyncView(ReindexBaseView):
    def __call__(self):
        authenticator = getMultiAdapter(
            (self.context, self.request), name=u"authenticator"
        )
        if not authenticator.verify():
            raise Unauthorized
        # first of all reindex objects to solr
        # self.reindexPloneToSolr()

        # then remove no more present items on SOLR
        self.cleanupSolrIndex()


class ReindexProgressView(BrowserView):
    def __call__(self):
        self.request.response.setHeader('Content-Type', 'application/json')
        return json.dumps(self.status)

    @property
    def status(self):
        annotations = IAnnotations(api.portal.get())
        return dict(annotations.get('solr_reindex', {}))


class ReindexSolrView(BrowserView):
    @property
    def token(self):
        return createToken()
