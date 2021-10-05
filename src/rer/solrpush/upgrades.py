# -*- coding: utf-8 -*-
from plone import api
from plone.app.upgrade.utils import installOrReinstallProduct
from rer.solrpush.utils.solr_common import init_solr_push
from rer.solrpush.utils.solr_indexer import push_to_solr

import logging

logger = logging.getLogger(__name__)

default_profile = "profile-rer.solrpush:default"


def update_profile(context, name):
    setup_tool = api.portal.get_tool(name="portal_setup")
    setup_tool.runImportStepFromProfile(default_profile, name)


def update_registry(context):
    update_profile(context=context, name="plone.app.registry")


def update_controlpanel(context):
    update_profile(context=context, name="controlpanel")


def update_actions(context):
    update_profile(context=context, name="actions")


def to_1100(context):
    setup_tool = api.portal.get_tool(name="portal_setup")
    setup_tool.runAllImportStepsFromProfile("profile-rer.solrpush:to_1100")
    setup_tool.runImportStepFromProfile(default_profile, "plone.app.registry")


def to_1200(context):
    setup_tool = api.portal.get_tool(name="portal_setup")
    setup_tool.runImportStepFromProfile(default_profile, "plone.app.registry")
    setup_tool.runImportStepFromProfile(default_profile, "rolemap")
    setup_tool.runImportStepFromProfile(default_profile, "controlpanel")


def to_1300(context):
    setup_tool = api.portal.get_tool(name="portal_setup")
    setup_tool.runAllImportStepsFromProfile("profile-rer.solrpush:to_1300")


def to_1400(context):
    installOrReinstallProduct(
        api.portal.get(), "collective.z3cform.jsonwidget"
    )
    update_registry(context)
    update_controlpanel(context)


def to_1600(context):
    # add new criteria
    update_registry(context)
    # reload schema
    init_solr_push()
    brains = api.content.find(portal_type=["File", "Image"])
    tot = len(brains)
    logger.info("Reindexing {} contents for updated mime_types.".format(tot))
    i = 0

    for brain in brains:
        i += 1
        if i % 500 == 0:
            logger.info("[PROGRESS] - {}/{}".format(i, tot))
        item = brain.getObject()
        try:
            push_to_solr(item)
        except Exception:
            # solr can't index it, pass
            continue
