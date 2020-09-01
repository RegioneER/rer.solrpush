# -*- coding: utf-8 -*-
from plone import api


def to_1100(context):
    setupTool = api.portal.get_tool(name="portal_setup")
    setupTool.runAllImportStepsFromProfile("profile-rer.solrpush:1100")
