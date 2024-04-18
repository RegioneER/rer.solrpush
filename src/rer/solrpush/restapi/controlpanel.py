from plone.restapi.controlpanels import RegistryConfigletPanel
from rer.solrpush.interfaces import IElevateSettings
from rer.solrpush.interfaces import IRerSolrpushLayer
from rer.solrpush.interfaces import IRERSolrpushRestapiControlpanel
from rer.solrpush.interfaces.settings import IRerSolrpushSettings
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface


@adapter(Interface, IRerSolrpushLayer)
@implementer(IRERSolrpushRestapiControlpanel)
class RerSolrpushSettingsControlpanel(RegistryConfigletPanel):
    schema = IRerSolrpushSettings
    configlet_id = "SolrPushSettings"
    configlet_category_id = "Products"
    schema_prefix = None


@adapter(Interface, IRerSolrpushLayer)
@implementer(IRERSolrpushRestapiControlpanel)
class ElevateSettingsControlpanel(RegistryConfigletPanel):
    schema = IElevateSettings
    configlet_id = "SolrPushElevate"
    configlet_category_id = "Products"
    schema_prefix = None
