# -*- coding: utf-8 -*-
from plone import api

default_profile = "profile-rer.solrpush:default"


def update_profile(context, name):
    setup_tool = api.portal.get_tool(name="portal_setup")
    setup_tool.runImportStepFromProfile(default_profile, name)


def update_registry(context):
    update_profile(context=context, name="plone.app.registry")


def to_1100(context):
    setup_tool = api.portal.get_tool(name="portal_setup")
    setup_tool.runAllImportStepsFromProfile("profile-rer.solrpush:to_1100")
    setup_tool.runImportStepFromProfile(default_profile, "plone.app.registry")


def to_1200(context):
    setup_tool = api.portal.get_tool(name="portal_setup")
    setup_tool.runImportStepFromProfile(default_profile, "plone.app.registry")
    setup_tool.runImportStepFromProfile(default_profile, "rolemap")
    setup_tool.runImportStepFromProfile(default_profile, "controlpanel")
