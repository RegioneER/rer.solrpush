# -*- coding: utf-8 -*-
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.app.registry.browser.controlpanel import RegistryEditForm
from rer.solrpush import _
from rer.solrpush.interfaces import IElevateSettings
from z3c.form import field
from collective.z3cform.datagridfield import DataGridFieldFactory


class ElevateSettingsEditForm(RegistryEditForm):

    schema = IElevateSettings
    label = _(
        "solr_elevate_configuration_label",
        default=u"Solr Push Elevate Configuration",
    )

    fields = field.Fields(IElevateSettings)
    fields["elevate_schema"].widgetFactory = DataGridFieldFactory


class ElevateSettingsView(ControlPanelFormWrapper):
    form = ElevateSettingsEditForm
