# -*- coding: utf-8 -*-
from plone import api

default_profile = "profile-rer.solrpush:default"


def to_1100(context):
    setup_tool = api.portal.get_tool(name="portal_setup")
    setup_tool.runAllImportStepsFromProfile("profile-rer.solrpush:to_1100")
    setup_tool.runImportStepFromProfile(default_profile, "plone.app.registry")

def to_1200(context):
    setup_tool = api.portal.get_tool(name="portal_setup")
    setup_tool.runAllImportStepsFromProfile("profile-rer.solrpush:1200")
    setup_tool.runImportStepFromProfile(default_profile, "plone.app.registry")
