# -*- coding: utf-8 -*-
"""Module where all interfaces, events and exceptions live."""

from rer.solrpush import _
from zope import schema
from zope.interface import Interface
from zope.publisher.interfaces.browser import IDefaultBrowserLayer


class IRerSolrpushLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""


class IRerSolrpushConf(Interface):
    """
    """

    solr_url = schema.TextLine(
        title=_(u"URL SOLR"),
        description=_(u"The SOLR URL to connect to"),
        required=False)

    enabled_types = schema.List(
        title=_(u'enabled_types_label',
                default=u'Enabled portal types'),
        description=_(u'enabled_types_help',
                      default=u'Select a list of portal types to index in solr.'),  # noqa
        required=False,
        default=[],
        missing_value=[],
        value_type=schema.Choice(
            vocabulary='plone.app.vocabularies.PortalTypes',
        ),
    )


class IRerSolrpushSettings(IRerSolrpushConf):
    """
    Marker interface for settings
    """
