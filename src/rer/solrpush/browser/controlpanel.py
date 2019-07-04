# -*- coding: utf-8 -*-
"""
Modulo per il pannello di configurazione di solr.
"""

from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.app.registry.browser.controlpanel import RegistryEditForm
from rer.solrpush import _
from rer.solrpush.interfaces import IRerSolrpushConf
from rer.solrpush.interfaces import IRerSolrpushSettings
from z3c.form import field
from z3c.form import group


class FormConfConnessione(group.Group):
    label = _(u"Connection")
    fields = field.Fields(IRerSolrpushConf)


class RerSolrpushEditForm(RegistryEditForm):

    schema = IRerSolrpushSettings
    groups = (FormConfConnessione, )
    label = _(u"Solr Push Configuration")

    def updateFields(self):
        super(RerSolrpushEditForm, self).updateFields()
        self.groups[0].fields = self.groups[0].fields.select(
            'active',
            'solr_url',
            'site_id',
            'enabled_types'
        )


class RerSolrpushView(ControlPanelFormWrapper):
    form = RerSolrpushEditForm
