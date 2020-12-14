# -*- coding: utf-8 -*-
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.app.registry.browser.controlpanel import RegistryEditForm
from rer.solrpush import _
from rer.solrpush.interfaces import IElevateSettings
from z3c.form import field
from collective.z3cform.jsonwidget.browser.widget import JSONFieldWidget
from rer.solrpush.interfaces.elevate import IElevateRowSchema
from Products.CMFPlone.resources import add_bundle_on_request


class ElevateSettingsEditForm(RegistryEditForm):

    schema = IElevateSettings
    label = _(
        "solr_elevate_configuration_label",
        default=u"Solr Push Elevate Configuration",
    )

    fields = field.Fields(IElevateSettings)
    fields["elevate_schema"].widgetFactory = JSONFieldWidget

    def updateWidgets(self):
        """
        Hide some fields
        """
        super(ElevateSettingsEditForm, self).updateWidgets()
        self.widgets["elevate_schema"].schema = IElevateRowSchema


class ElevateSettingsView(ControlPanelFormWrapper):
    form = ElevateSettingsEditForm

    def __call__(self):
        add_bundle_on_request(self.request, "z3cform-jsonwidget-bundle")
        return super(ElevateSettingsView, self).__call__()
