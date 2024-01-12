from rer.solrpush.interfaces import IRerSolrpushLayer
from rer.solrpush.interfaces.settings import IRerSolrpushSettings
from rer.solrpush.interfaces import IRERSolrpushRestapiControlpanel
from plone.restapi.controlpanels import RegistryConfigletPanel
from zope.component import adapter
from zope.interface import Interface
from zope.interface import implementer


@adapter(Interface, IRerSolrpushLayer)
@implementer(IRERSolrpushRestapiControlpanel)
class RerSolrpushSettingsControlpanel(RegistryConfigletPanel):
    schema = IRerSolrpushSettings
    configlet_id = "SolrPushSettings"
    configlet_category_id = "Products"
    schema_prefix = None
