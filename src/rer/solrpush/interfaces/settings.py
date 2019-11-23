# -*- coding: utf-8 -*-
from lxml.etree import fromstring
from lxml.etree import XMLSyntaxError

# from plone.autoform import directives
from plone.supermodel import model
from rer.solrpush import _

# from rer.solrpush.browser.solr_fields import SolrFieldsFieldWidget
from zope import schema
from zope.interface import Invalid


def elevateConstraint(value):
    """Check if is a valid xml
    """
    try:
        fromstring(value)
        return True
    except XMLSyntaxError as e:
        raise Invalid(e.message)


class IRerSolrpushConf(model.Schema):
    """
    """

    active = schema.Bool(
        title=_(u"Active"),
        description=_(u"Enable SOLR indexing on this site."),
        required=False,
        default=False,
    )

    solr_url = schema.TextLine(
        title=_(u"SOLR url"),
        description=_(u"The SOLR core to connect to."),
        required=True,
    )

    frontend_url = schema.TextLine(
        title=_(u"Frontend url"),
        description=_(u"If the website has different URL for frontend users."),
        required=False,
    )

    enabled_types = schema.List(
        title=_(u'enabled_types_label', default=u'Enabled portal types'),
        description=_(
            u'enabled_types_help',
            default=u'Select a list of portal types to index in solr. '
            u'Empty list means that all portal types will be indexed.',
        ),
        required=False,
        default=[],
        missing_value=[],
        value_type=schema.Choice(
            vocabulary='plone.app.vocabularies.PortalTypes'
        ),
    )

    # elevate_xml = schema.Text(
    #     title=u'Configurazione elevate',
    #     description=u'Inserisci una configurazione per l\'elevate come '
    #     u'se fosse un file xml.',
    #     required=False,
    #     constraint=elevateConstraint,
    # )

    # enable_query_debug = schema.Bool(
    #     title=u'Abilita il debug delle query solr',
    #     description=u'Se selezionato, mostra la query effettuata su solr, '
    #     u'per il debug. Solo per gli amministratori del sito.',
    #     required=False,
    # )

    # directives.widget(index_fields=SolrFieldsFieldWidget)
    index_fields = schema.SourceText(
        title=_(
            'index_fields_label',
            default=u'List of fields loaded from SOLR that we use for indexing.',
        ),
        description=_(
            u'index_fields_help',
            default=u'We store this list for performance'
            u' reasons. If the configuration changes, you need to click on'
            u' Reload button',
        ),
        required=False,
    )

    # NASCOSTO DAL PANNELLO DI CONTROLLO (vedi: browser/controlpanel.py)
    ready = schema.Bool(
        title=_(u"Ready"),
        description=_(u"SOLR push is ready to be used."),
        required=False,
        default=False,
    )


class IRerSolrpushSettings(IRerSolrpushConf):
    """
    Marker interface for settings
    """
