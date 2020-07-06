# -*- coding: utf-8 -*-
from AccessControl import Unauthorized
from persistent.dict import PersistentDict
from plone import api
from plone.memoize import ram
from plone.memoize.view import memoize
from plone.protect.authenticator import createToken
from Products.CMFCore.interfaces import IIndexQueueProcessor
from Products.Five import BrowserView
from pysolr import SolrError
from rer.solrpush import _
from rer.solrpush.solr import is_solr_active
from rer.solrpush.solr import push_to_solr
from rer.solrpush.solr import remove_from_solr
from rer.solrpush.solr import reset_solr
from rer.solrpush.solr import search
from time import strftime
from time import time
from time import sleep
from transaction import commit
from z3c.form import button
from z3c.form import form
from zope.annotation.interfaces import IAnnotations
from zope.component import getMultiAdapter
from zope.component import getSiteManager
from zope.i18n import translate

import logging
import json
import pkg_resources


JS_TEMPLATE = "{portal_url}/++plone++rer.solrpush/dist/{env_mode}/{name}.js?v={version}"
CSS_TEMPLATE = (
    "{portal_url}/++plone++rer.solrpush/dist/{env_mode}/{name}.css?v={version}"
)


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

    @button.buttonAndHandler(_("start_label", default=u"Start"))
    def handleApply(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        self.do_action()

    @button.buttonAndHandler(_("cancel_label", default=u"Cancel"))
    def handleCancel(self, action):
        msg_label = _("maintenance_cancel_action", default="Action cancelled")
        api.portal.show_message(message=msg_label, request=self.request)
        return self.request.response.redirect(
            "{}/@@solrpush-conf".format(api.portal.get().absolute_url())
        )


class ResetSolr(SolrMaintenanceBaseForm):
    """
    Reset solr index
    """

    label = _("maintenance_reset_solr_label", default="Reset SOLR index")
    description = _(
        "maintenance_reset_solr_description", default="Drop all items in SOLR index."
    )

    def do_action(self):
        reset_solr()
        msg_label = _("maintenance_reset_success", default="SOLR index dropped")
        logger.info("##### SOLR Index dropped #####")
        api.portal.show_message(message=msg_label, request=self.request)
        return self.request.response.redirect(
            "{}/@@solrpush-conf".format(api.portal.get().absolute_url())
        )


class ReindexBaseView(BrowserView):
    @property
    def solr_error_message(self):
        return translate(
            _(
                "solr_error_connection",
                default=u"There have been problems connecting to SOLR. "
                u"Contact site administrator.",
            ),
            context=self.request,
        )

    def setupAnnotations(self, items_len, message):
        annotations = IAnnotations(api.portal.get())
        annotations["solr_reindex"] = PersistentDict(
            {
                "in_progress": True,
                "tot": items_len,
                "counter": 0,
                "timestamp": strftime("%Y/%m/%d-%H:%M:%S "),
                "message": message,
            }
        )
        commit()
        return annotations["solr_reindex"]

    @property
    @memoize
    def solr_utility(self):
        sm = getSiteManager()
        return sm.queryUtility(IIndexQueueProcessor, name="solrpush.utility")

    def reindexPloneToSolr(self):
        if not self.solr_utility:
            return
        if not is_solr_active():
            logger.warning("Trying to reindexing but solr is not set as active")
            return
        elapsed = timer()
        if self.solr_utility.enabled_types:
            brains_to_reindex = api.content.find(
                portal_type=self.solr_utility.enabled_types
            )
        else:
            pc = api.portal.get_tool(name="portal_catalog")
            brains_to_reindex = pc()
        status = self.setupAnnotations(
            items_len=brains_to_reindex.actual_result_count,
            message="Sync items to SOLR",
        )
        logger.info("##### SOLR REINDEX START #####")
        logger.info(
            "Reindexing {} items.".format(brains_to_reindex.actual_result_count)
        )
        for i, brain in enumerate(brains_to_reindex):
            status["counter"] = status["counter"] + 1
            commit()
            obj = brain.getObject()
            try:
                push_to_solr(obj)
                logger.info(
                    "[{index}/{total}] {path} ({type})".format(
                        index=i + 1,
                        total=brains_to_reindex.actual_result_count,
                        path=brain.getPath(),
                        type=brain.portal_type,
                    )
                )

            except SolrError:
                # maybe solr can't handle too much requests
                sleep(10)
                try:
                    push_to_solr(obj)
                    logger.info(
                        "[{index}/{total}] {path} ({type})".format(
                            index=i + 1,
                            total=brains_to_reindex.actual_result_count,
                            path=brain.getPath(),
                            type=brain.portal_type,
                        )
                    )
                except SolrError:
                    status["in_progress"] = False
                    status["error"] = True
                    status["message"] = self.solr_error_message
                    return
        status["in_progress"] = False
        elapsed_time = next(elapsed)
        logger.info("SOLR Reindex completed in {}".format(elapsed_time))

    def cleanupSolrIndex(self):
        if not self.solr_utility:
            return
        if not is_solr_active():
            logger.warning("Trying to cleanup but solr is not set as active")
            return
        elapsed = timer()
        pc = api.portal.get_tool(name="portal_catalog")
        if self.solr_utility.enabled_types:
            brains_to_sync = api.content.find(
                portal_type=self.solr_utility.enabled_types
            )
        else:
            pc = api.portal.get_tool(name="portal_catalog")
            brains_to_sync = pc()
        good_uids = [x.UID for x in brains_to_sync]
        solr_results = search(query={"*": "*", "b_size": 100000}, fl="UID")
        uids_to_cleanup = [
            x["UID"] for x in solr_results.docs if x["UID"] not in good_uids
        ]
        status = self.setupAnnotations(
            items_len=len(uids_to_cleanup), message="Cleanup items on SOLR"
        )
        logger.info("##### SOLR CLEANUP STARTED #####")
        logger.info(" - First of all, cleanup items on SOLR")
        for uid in uids_to_cleanup:
            remove_from_solr(uid)
            status["counter"] = status["counter"] + 1
            commit()

        status["in_progress"] = False
        elapsed_time = next(elapsed)
        logger.info("SOLR indexes cleanup completed in {}".format(elapsed_time))


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
        self.cleanupSolrIndex()
        self.reindexPloneToSolr()


class ReindexProgressView(BrowserView):
    def __call__(self):
        self.request.response.setHeader("Content-Type", "application/json")
        return json.dumps(self.status)

    @property
    def status(self):
        annotations = IAnnotations(api.portal.get())
        return dict(annotations.get("solr_reindex", {}))


# REACT VIEWS
class ReactView(BrowserView):
    """ """

    @ram.cache(lambda *args: time() // (60 * 60))
    def get_version(self):
        return pkg_resources.get_distribution("rer.solrpush").version

    def get_env_mode(self):
        return (
            api.portal.get_registry_record("plone.resources.development")
            and "dev"  # noqa
            or "prod"  # noqa
        )

    def get_resource_js(self, name="main"):
        return JS_TEMPLATE.format(
            portal_url=api.portal.get().absolute_url(),
            env_mode=self.get_env_mode(),
            name=name,
            version=self.get_version(),
        )

    def get_resource_css(self, name="main"):
        return CSS_TEMPLATE.format(
            portal_url=api.portal.get().absolute_url(),
            env_mode=self.get_env_mode(),
            name=name,
            version=self.get_version(),
        )

    @property
    def token(self):
        return createToken()

    @property
    def is_active(self):
        return is_solr_active()


class ReindexSolrView(ReactView):

    label = _("maintenance_reindex_label", default="Reindex SOLR")
    description = _(
        "maintenance_reindex_help",
        default="Get all Plone contents and reindex them on SOLR.",
    )
    action = "do-reindex"


class SyncSolrView(ReactView):

    label = _("maintenance_sync_label", default="Sync SOLR")
    description = _(
        "maintenance_sync_help",
        default="Remove no more existing contents from SOLR and sync with Plone.",  # noqa
    )
    action = "do-sync"
