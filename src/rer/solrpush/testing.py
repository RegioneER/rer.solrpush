# -*- coding: utf-8 -*-
from plone.api.portal import set_registry_record
from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.restapi.testing import PloneRestApiDXLayer
from plone.testing import Layer
from plone.testing import z2
from rer.solrpush.interfaces.settings import IRerSolrpushSettings
from rer.solrpush.utils import init_solr_push
from time import sleep
from urllib.error import URLError
from urllib.request import Request
from urllib.request import urlopen
from ZPublisher.HTTPRequest import HTTPRequest

import plone.restapi
import rer.solrpush


class SolrLayer(Layer):
    """Solr test layer: it expects a Solr instance already running
    (see docker-compose.yml) and waits until it answers to ping.
    """

    def __init__(
        self,
        bases=None,
        name="Solr Layer",
        module=None,
        solr_host="localhost",
        solr_port=8983,
        solr_base="/solr/solrpush_test",
    ):
        super(SolrLayer, self).__init__(bases, name, module)
        self.solr_host = solr_host
        self.solr_port = solr_port
        self.solr_base = solr_base
        self.solr_url = "http://{0}:{1}{2}".format(solr_host, solr_port, solr_base)

    def setUp(self):
        """Poll Solr until it is up and running."""
        solr_ping_url = "{0}/admin/ping?wt=xml".format(self.solr_url)
        for i in range(10):
            try:
                result = urlopen(solr_ping_url)
                if result.code == 200 and b'<str name="status">OK</str>' in (
                    result.read()
                ):
                    return
            except URLError:
                pass
            sleep(3)
        raise RuntimeError(
            "Solr is not reachable at {0}: start it with "
            "`docker compose up -d`.".format(self.solr_url)
        )

    def tearDown(self):
        """Clean Solr test core."""
        request = Request(
            "{0}/update?commit=true".format(self.solr_url),
            data=b'{"delete": {"query": "*:*"}}',
            headers={"Content-Type": "application/json"},
        )
        urlopen(request)


SOLR_FIXTURE = SolrLayer()


class RerSolrpushRestApiLayer(PloneRestApiDXLayer):
    """ """

    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)

    def __init__(
        self,
        bases=None,
        name="SolrPush Layer",
        module=None,
        solr_host="localhost",
        solr_port=8983,
        solr_base="/solr/solrpush_test",
    ):
        super().__init__(bases, name, module)
        self.solr_host = solr_host
        self.solr_port = solr_port
        self.solr_base = solr_base
        # SolrLayer should use the same settings as CollectiveSolrLayer
        self.solr_layer = SolrLayer(
            bases,
            name,
            module,
            solr_host=solr_host,
            solr_port=solr_port,
            solr_base=solr_base,
        )

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.
        self._orig_retry_max_count = HTTPRequest.retry_max_count
        HTTPRequest.retry_max_count = 3

        self.loadZCML(package=rer.solrpush)
        self.loadZCML(package=plone.restapi)

    def tearDownZope(self, app):
        HTTPRequest.retry_max_count = self._orig_retry_max_count

    def setUpPloneSite(self, portal):
        self.solr_layer.setUp()
        applyProfile(portal, "rer.solrpush:default")
        set_registry_record("active", True, interface=IRerSolrpushSettings)
        set_registry_record(
            "solr_url",
            self.solr_layer.solr_url,
            interface=IRerSolrpushSettings,
        )
        init_solr_push()

    def tearDownPloneSite(self, portal):
        set_registry_record("active", True, interface=IRerSolrpushSettings)
        set_registry_record(
            "solr_url",
            self.solr_layer.solr_url,
            interface=IRerSolrpushSettings,
        )
        self.solr_layer.tearDown()


RER_SOLRPUSH_API_FIXTURE = RerSolrpushRestApiLayer()
RER_SOLRPUSH_API_INTEGRATION_TESTING = IntegrationTesting(
    bases=(RER_SOLRPUSH_API_FIXTURE,),
    name="RerSolrpushRestApiLayer:Integration",
)

RER_SOLRPUSH_API_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(RER_SOLRPUSH_API_FIXTURE, z2.ZSERVER_FIXTURE),
    name="RerSolrpushRestApiLayer:Functional",
)
