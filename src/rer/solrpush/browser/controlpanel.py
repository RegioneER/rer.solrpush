# -*- coding: utf-8 -*-
"""
Modulo per il pannello di configurazione di solr.
"""

from plone import api
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.app.registry.browser.controlpanel import RegistryEditForm
from rer.solrpush import _
from rer.solrpush.interfaces import IRerSolrpushConf
from rer.solrpush.interfaces import IRerSolrpushSettings
from rer.solrpush.solr import init_solr_push
from z3c.form import button
from z3c.form import field
from z3c.form import group
from z3c.form.interfaces import DISPLAY_MODE

import logging

logger = logging.getLogger(__name__)


class FormConfConnessione(group.Group):
    label = _(u"Connection")
    fields = field.Fields(IRerSolrpushConf)


class RerSolrpushEditForm(RegistryEditForm):
    """ Nel form del pannello di controllo mettiamo anche le logiche per
    il caricamento
    """

    schema = IRerSolrpushSettings
    groups = (FormConfConnessione,)
    label = _(u"Solr Push Configuration")

    formErrorsMessage = (
        "Sono presenti degli errori, si prega di ricontrollare i dati inseriti"
    )  # noqa

    def updateFields(self):
        super(RerSolrpushEditForm, self).updateFields()
        # self.groups[0].fields = self.groups[0].fields.select(
        #     'active',
        #     'solr_url',
        #     'frontend_url',
        #     'enabled_types',
        #     'elevate_xml',
        #     'enable_query_debug',
        #     'index_fields',
        # )
        self.groups[0].fields['index_fields'].mode = DISPLAY_MODE
        self.groups[0].fields['ready'].mode = DISPLAY_MODE

    @button.buttonAndHandler(_("Save"), name=None)
    def handleSave(self, action):
        super(RerSolrpushEditForm, self).handleSave(self, action)
        # self.save()

    @button.buttonAndHandler(_("Cancel"), name="cancel")
    def handleCancel(self, action):
        super(RerSolrpushEditForm, self).handleCancel(self, action)

    @button.buttonAndHandler(_("Load schema.xml"), name="reload")
    def handleReload(self, action):
        data, errors = self.extractData()

        ErrorMessage = _('There were problems when updating the schema.')

        solr_url = api.portal.get_registry_record(
            'rer.solrpush.interfaces.IRerSolrpushSettings.solr_url',
            default=False,
        )
        if solr_url:
            outcome = init_solr_push(solr_url)
            if outcome:
                errors = True
                ErrorMessage = outcome
        else:
            errors = True

        if errors:
            api.portal.show_message(
                message=ErrorMessage, request=self.request, type='error'
            )
            return False

        api.portal.show_message(
            message=_('Schema ricaricatone!'),
            request=self.request,
            type='info',
        )

        return True

    def save(self):
        # TODO - Eliminare questo metodo se non viene più usato alla fine
        # perchè logiche spostate nell'altro bottone
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return False

        solr_url_reg = api.portal.get_registry_record(
            'rer.solrpush.interfaces.IRerSolrpushSettings.solr_url',
            default=False,
        )

        if data.get('solr_url', '') != solr_url_reg:
            # TODO - QUI lanciamo l'inizializzazione del prodotto
            pass

        self.applyChanges(data)

        return True


class RerSolrpushView(ControlPanelFormWrapper):
    form = RerSolrpushEditForm
