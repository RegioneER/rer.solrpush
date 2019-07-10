# -*- coding: utf-8 -*-
"""Module where all interfaces, events and exceptions live."""

from plone.supermodel import model
from rer.solrpush import _
from zope import schema
from zope.publisher.interfaces.browser import IDefaultBrowserLayer


class IRerSolrpushLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""


class IRerSolrpushConf(model.Schema):
    """
    """

    active = schema.Bool(
        title=_(u"Active"),
        description=_(u"SOLR push indexing activation"),
        required=False,
        default=False,
    )

    solr_url = schema.TextLine(
        title=_(u"URL SOLR"),
        description=_(u"The SOLR URL to connect to"),
        required=True)

    frontend_url = schema.TextLine(
        title=_(u"Frontend url"),
        description=_(u"If the website has different URL for frontend users"),
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

    # questo campo è la lista dei field letti direttamente dall'xml di solr
    # TODO - rendere questo campo "read only" nel pannello
    index_fields = schema.List(
        title=_(u'index_fields_label',
                default=u'Fields list read from SOLR xml schema.'),
        description=_(u'index_fields_help',
                      default=u"DON'T CHANGE THIS MANUALLY"),
        required=False,
        value_type=schema.TextLine(),
    )

    # NASCOSTO DAL PANNELLO DI CONTROLLO (vedi: browser/controlpanel.py)
    ready = schema.Bool(
        title=_(u"Ready"),
        description=_(u"SOLR push is ready to be used"),
        required=False,
        default=False,
    )


class IRerSolrpushSettings(IRerSolrpushConf):
    """
    Marker interface for settings
    """
