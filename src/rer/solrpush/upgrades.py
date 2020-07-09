# -*- coding: utf-8 -*-
from plone import api

DEFAULT_PROFILE = "profile-rer.solrpush:default"


def update_profile(profile_id, dependencies=False):
    setup_tool = api.portal.get_tool("portal_setup")
    setup_tool.runImportStepFromProfile(
        DEFAULT_PROFILE, profile_id, run_dependencies=dependencies
    )


def update_registry(context):
    update_profile(profile_id="plone.app.registry")
