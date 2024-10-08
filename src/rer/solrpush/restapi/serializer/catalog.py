from plone.restapi.interfaces import ISerializeToJson
from plone.restapi.serializer.catalog import (
    LazyCatalogResultSerializer as BaseSerializer,
)
from rer.solrpush.parser import SolrResponse
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface


@implementer(ISerializeToJson)
@adapter(SolrResponse, Interface)
class LazyCatalogResultSerializerSOLR(BaseSerializer):
    """"""
