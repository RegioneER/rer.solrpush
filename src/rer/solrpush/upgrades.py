# -*- coding: utf-8 -*-
from plone import api
from plone.app.upgrade.utils import installOrReinstallProduct

default_profile = "profile-rer.solrpush:default"


def update_profile(context, name):
    setup_tool = api.portal.get_tool(name="portal_setup")
    setup_tool.runImportStepFromProfile(default_profile, name)


def update_registry(context):
    update_profile(context=context, name="plone.app.registry")


def update_controlpanel(context):
    update_profile(context=context, name="controlpanel")


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
