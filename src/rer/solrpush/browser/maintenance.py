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
from rer.solrpush.utils import push_to_solr
from rer.solrpush.utils import remove_from_solr
from rer.solrpush.utils import reset_solr
from rer.solrpush.utils import search
from rer.solrpush.utils.solr_common import is_solr_active
from rer.solrpush.utils.solr_indexer import can_index
from rer.solrpush.utils.solr_indexer import get_site_title
from rer.solrpush.utils.solr_indexer import parse_date_as_datetime
from time import strftime
from time import time
from transaction import commit
from z3c.form import button
from z3c.form import form
from zope.annotation.interfaces import IAnnotations
from zope.component import getMultiAdapter
from zope.component import getSiteManager
from zope.i18n import translate

import json
import logging
import os
import pkg_resources


JS_TEMPLATE = (
    "{portal_url}/++plone++rer.solrpush/dist/{env_mode}/{name}.js?v={version}"
)
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
            "{}/@@solrpush-settings".format(api.portal.get().absolute_url())
        )


class ResetSolr(SolrMaintenanceBaseForm):
    """
    Reset solr index
    """

    label = _("maintenance_reset_solr_label", default="Reset SOLR index")
    description = _(
        "maintenance_reset_solr_description",
        default="Drop all items in SOLR index.",
    )

    def do_action(self):
        reset_solr()
        msg_label = _(
            "maintenance_reset_success", default="SOLR index dropped"
        )
        logger.info("##### SOLR Index dropped #####")
        api.portal.show_message(message=msg_label, request=self.request)
        return self.request.response.redirect(
            "{}/@@solrpush-settings".format(api.portal.get().absolute_url())
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
            logger.warning(
                "Trying to reindexing but solr is not set as active"
            )
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
            "Reindexing {} items.".format(
                brains_to_reindex.actual_result_count
            )
        )
        skipped = 0
        indexed = 0
        for brain in brains_to_reindex:
            tot_indexed = indexed + skipped + 1
            commit()
            obj = brain.getObject()
            try:
                res = push_to_solr(obj)
            except Exception as e:
                logger.exception(e)
                status["in_progress"] = False
                status["error"] = True
                status["message"] = self.solr_error_message
                return
            if res:
                indexed += 1
            else:
                skipped += 1
            logger.debug(
                "[{indexed}/{total}] {path} ({type})".format(
                    indexed=tot_indexed,
                    total=brains_to_reindex.actual_result_count,
                    path=brain.getPath(),
                    type=brain.portal_type,
                )
            )
            if tot_indexed > 0 and tot_indexed % 200 == 0:
                logger.info(
                    "[PROGRESS]: {}/{}".format(
                        tot_indexed, brains_to_reindex.actual_result_count
                    )
                )
            status["counter"] = tot_indexed

        status["in_progress"] = False
        elapsed_time = next(elapsed)
        logger.info("SOLR Reindex completed in {}".format(elapsed_time))

    def removeZombiesFromSolr(self, disable_progress=False):
        """
        remove items stored in solr that are no longer present in Plone or
        they are not indexeable anymore.
        """
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
        solr_results = search(
            query={"site_name": get_site_title(), "b_size": 100000000},
            fl="UID",
        )
        uids_to_remove = [
            x["UID"] for x in solr_results.docs if x["UID"] not in good_uids
        ]
        if not disable_progress:
            status = self.setupAnnotations(
                items_len=len(uids_to_remove), message="Cleanup items on SOLR"
            )
        logger.info("##### CLEANUP CONTENTS FROM SOLR #####")
        for uid in uids_to_remove:
            remove_from_solr(uid)
            if not disable_progress:
                status["counter"] = status["counter"] + 1
                commit()

        if not disable_progress:
            status["in_progress"] = False
        elapsed_time = next(elapsed)
        logger.info("Completed in {}.".format(elapsed_time))
        if len(uids_to_remove):
            logger.info(
                "Removed {} items from SOLR that are no longer in Plone".format(
                    len(uids_to_remove)
                )
            )

    def syncPloneWithSolr(self, disable_progress=False):
        if not self.solr_utility:
            return
        if not is_solr_active():
            logger.warning("Trying to cleanup but solr is not set as active")
            return
        elapsed = timer()
        logger.info("##### SYNC CONTENTS TO SOLR #####")
        pc = api.portal.get_tool(name="portal_catalog")
        solr_docs = search(
            query={"site_name": get_site_title(), "b_size": 100000000},
            fl="UID modified",
        ).docs
        solr_items = {item["UID"]: item["modified"] for item in solr_docs}
        if self.solr_utility.enabled_types:
            brains_to_sync = api.content.find(
                portal_type=self.solr_utility.enabled_types
            )
        else:
            pc = api.portal.get_tool(name="portal_catalog")
            brains_to_sync = pc()
        results = self.sync_contents(
            brains_to_sync=brains_to_sync,
            solr_items=solr_items,
            disable_progress=disable_progress,
        )
        elapsed_time = next(elapsed)
        logger.info("Completed in {}.".format(elapsed_time))
        if len(results["indexed"]):
            logger.info(
                "Indexed {} items (new or modified):".format(
                    len(results["indexed"])
                )
            )
            for path in results["indexed"]:
                logger.info("- {}".format(path))
        if len(results["removed"]):
            logger.info(
                "Removed {} items (no more indexeable):".format(
                    len(results["removed"])
                )
            )
            for path in results["removed"]:
                logger.info("- {}".format(path))
        if len(results["not_indexed"]):
            logger.info(
                "NOT indexed {} items (errors):".format(
                    len(results["not_indexed"])
                )
            )
            for error in results["not_indexed"]:
                logger.info(
                    "- {path} ({message})".format(
                        path=error.get("path", ""),
                        message=error.get("message", "Undefined Error"),
                    )
                )

    def sync_contents(
        self, brains_to_sync, solr_items, disable_progress=False
    ):
        indexed = []
        not_indexed = []
        removed = []
        if not disable_progress:
            status = self.setupAnnotations(
                items_len=len(brains_to_sync), message="Sync contents to SOLR"
            )
        for brain in brains_to_sync:
            if not disable_progress:
                status["counter"] = status["counter"] + 1
                commit()
            item = brain.getObject()
            if brain.UID not in solr_items:
                # missing from solr: try to index it
                try:
                    res = push_to_solr(item)
                    if res:
                        indexed.append(brain.getPath())
                except SolrError as e:
                    not_indexed.append(
                        {"path": brain.getPath(), "message": e.__str__()}
                    )
                except Exception as e:
                    not_indexed.append(
                        {"path": brain.getPath(), "message": str(e)}
                    )
            else:
                item = brain.getObject()
                if not can_index(item):
                    remove_from_solr(brain.UID)
                    removed.append(brain.getPath())
                    continue
                if (
                    parse_date_as_datetime(brain.modified)
                    != solr_items[brain.UID]  # noqa
                ):
                    # item has been modified and not synced in solr
                    try:
                        res = push_to_solr(item)
                        if res:
                            indexed.append(brain.getPath())
                    except Exception as e:
                        not_indexed.append(
                            {"path": brain.getPath(), "message": str(e)}
                        )
        if not disable_progress:
            status["in_progress"] = False
        return {
            "indexed": indexed,
            "not_indexed": not_indexed,
            "removed": removed,
        }


class DoReindexView(ReindexBaseView):
    def __call__(self):
        authenticator = getMultiAdapter(
            (self.context, self.request), name=u"authenticator"
        )
        if not authenticator.verify():
            raise Unauthorized
        # disable noisy logging from pysolr
        debug = os.environ.get("DEBUG_SOLR", "").lower() not in ("true", "1")
        if debug:
            pysolr_logger = logging.getLogger("pysolr")
            pt_logger = logging.getLogger("PortalTransforms")
            pysolr_logger.setLevel(logging.WARNING)
            pt_logger.setLevel(logging.WARNING)

        self.reindexPloneToSolr()
        if debug:
            pysolr_logger.setLevel(logging.INFO)
            pt_logger.setLevel(logging.INFO)


class DoSyncView(ReindexBaseView):
    def __call__(self, cron_view=False):
        if not cron_view:
            authenticator = getMultiAdapter(
                (self.context, self.request), name=u"authenticator"
            )
            if not authenticator.verify():
                raise Unauthorized
        # disable noisy logging from pysolr
        if os.environ.get("DEBUG_SOLR", "").lower() not in ("true", "1"):
            pysolr_logger = logging.getLogger("pysolr")
            pt_logger = logging.getLogger("PortalTransforms")
            pysolr_logger.setLevel(logging.WARNING)
            pt_logger.setLevel(logging.WARNING)

        self.removeZombiesFromSolr(disable_progress=cron_view)
        self.syncPloneWithSolr(disable_progress=cron_view)

        pysolr_logger.setLevel(logging.INFO)
        pt_logger.setLevel(logging.INFO)


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
