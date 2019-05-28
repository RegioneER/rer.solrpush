# -*- coding: utf-8 -*-
"""
Modulo per il pannello di configurazione di solr.
"""

from plone.supermodel import model
from zope import schema
from z3c.form import group
from z3c.form import field
from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper


class IRerSolrpushConf(model.Schema):

    solr_url = schema.TextLine(
        title=u"URL SOLR",
        description=u"Inserire qui l'url di SOLR a cui collegarsi",
        required=False)


class IRerSolrpushSettings(IRerSolrpushConf):
    """
    Marker interface for typology settings
    """


class FormConf(group.Group):
    label = u"Connessione"
    fields = field.Fields(IRerSolrpushConf)


class IRerSolrpushEditForm(RegistryEditForm):

    schema = IRerSolrpushSettings
    groups = (FormConf, )
    label = u"Configurazione Solr Push"


class IRerSolrpushView(ControlPanelFormWrapper):
    form = IRerSolrpushEditForm
