from plone.restapi.deserializer.controlpanels import ControlpanelDeserializeFromJson
from plone.restapi.interfaces import IDeserializeFromJson
from rer.solrpush.interfaces import IRERSolrpushRestapiControlpanel
from rer.solrpush.utils import check_solr_connection
from zope.component import adapter
from zope.interface import implementer


@implementer(IDeserializeFromJson)
@adapter(IRERSolrpushRestapiControlpanel)
class RERSolrpushControlpanelDeserializeFromJson(ControlpanelDeserializeFromJson):
    def __call__(self):
        super().__call__()
        check_solr_connection()
