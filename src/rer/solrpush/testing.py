# -*- coding: utf-8 -*-
from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from plone.testing import z2

import rer.solrpush


class RerSolrpushLayer(PloneSandboxLayer):

    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.
        import plone.restapi
        self.loadZCML(package=plone.restapi)
        self.loadZCML(package=rer.solrpush)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'rer.solrpush:default')


RER_SOLRPUSH_FIXTURE = RerSolrpushLayer()


RER_SOLRPUSH_INTEGRATION_TESTING = IntegrationTesting(
    bases=(RER_SOLRPUSH_FIXTURE,),
    name='RerSolrpushLayer:IntegrationTesting',
)


RER_SOLRPUSH_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(RER_SOLRPUSH_FIXTURE,),
    name='RerSolrpushLayer:FunctionalTesting',
)


RER_SOLRPUSH_ACCEPTANCE_TESTING = FunctionalTesting(
    bases=(
        RER_SOLRPUSH_FIXTURE,
        REMOTE_LIBRARY_BUNDLE_FIXTURE,
        z2.ZSERVER_FIXTURE,
    ),
    name='RerSolrpushLayer:AcceptanceTesting',
)
