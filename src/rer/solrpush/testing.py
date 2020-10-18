# -*- coding: utf-8 -*-
from plone.api.portal import set_registry_record
from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from rer.solrpush.interfaces.settings import IRerSolrpushSettings

import rer.solrpush


class RerSolrpushLayer(PloneSandboxLayer):

    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.
        self.loadZCML(package=rer.solrpush)

    def setUpPloneSite(self, portal):
        applyProfile(portal, "rer.solrpush:default")
        set_registry_record(
            "solr_url",
            "http://localhost:8983/solr/solrpush_test",
            interface=IRerSolrpushSettings,
        )


RER_SOLRPUSH_FIXTURE = RerSolrpushLayer()


RER_SOLRPUSH_INTEGRATION_TESTING = IntegrationTesting(
    bases=(RER_SOLRPUSH_FIXTURE,), name="RerSolrpushLayer:IntegrationTesting"
)


RER_SOLRPUSH_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(RER_SOLRPUSH_FIXTURE,), name="RerSolrpushLayer:FunctionalTesting"
)
