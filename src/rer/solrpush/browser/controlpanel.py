# -*- coding: utf-8 -*-
from plone import api
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.app.registry.browser.controlpanel import RegistryEditForm
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from rer.solrpush import _

# from rer.solrpush.interfaces.settings import IRerSolrpushConf
from rer.solrpush.interfaces.settings import IRerSolrpushSettings

# from rer.solrpush.browser.solr_fields import (
#     SolrFieldsWidget,
#     SolrFieldsFieldWidget,
# )
from rer.solrpush.solr import init_solr_push
from z3c.form import button

# from z3c.form import field
# from z3c.form import group
# from z3c.form.interfaces import DISPLAY_MODE
from z3c.form.interfaces import HIDDEN_MODE

import logging

logger = logging.getLogger(__name__)


# class FormConfConnessione(group.Group):
#     label = _(u"Connection")
#     fields = field.Fields(IRerSolrpushConf)


class RerSolrpushEditForm(RegistryEditForm):
    """ Nel form del pannello di controllo mettiamo anche le logiche per
    il caricamento
    """

    schema = IRerSolrpushSettings
    # groups = (FormConfConnessione,)
    label = _(u"Solr Push Configuration")

    formErrorsMessage = (
        "Sono presenti degli errori, si prega di ricontrollare i dati inseriti"
    )  # noqa

    def updateFields(self):
        super(RerSolrpushEditForm, self).updateFields()
        # self.groups[0].fields['index_fields'].mode = DISPLAY_MODE
        # self.groups[0].fields['ready'].mode = DISPLAY_MODE
        self.fields['index_fields'].mode = HIDDEN_MODE
        self.fields['ready'].mode = HIDDEN_MODE

    @button.buttonAndHandler(_("Save"), name=None)
    def handleSave(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        self.applyChanges(data)
        api.portal.show_message(_(u"Changes saved."), request=self.request)
        init_error = init_solr_push()
        if init_error:
            api.portal.show_message(
                init_error, type="error", request=self.request
            )
        else:
            api.portal.show_message(
                _(u"Loaded schema.xml from SOLR"), request=self.request
            )
        self.request.response.redirect(self.request.getURL())

    @button.buttonAndHandler(_("Cancel"), name="cancel")
    def handleCancel(self, action):
        super(RerSolrpushEditForm, self).handleCancel(self, action)

    @button.buttonAndHandler(_("Reload schema.xml"), name="reload")
    def handleReload(self, action):
        data, errors = self.extractData()

        init_error = init_solr_push()
        if init_error:
            api.portal.show_message(
                init_error, type="error", request=self.request
            )
        else:
            api.portal.show_message(
                _(u"Reloaded schema.xml from SOLR"), request=self.request
            )
        self.request.response.redirect(self.request.getURL())


class RerSolrpushView(ControlPanelFormWrapper):
    form = RerSolrpushEditForm
    index = ViewPageTemplateFile('templates/controlpanel_layout.pt')
