# -*- coding: utf-8 -*-
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.app.registry.browser.controlpanel import RegistryEditForm
from rer.solrpush import _
from rer.solrpush.interfaces import IElevateSettings
from z3c.form import field


class ElevateSettingsEditForm(RegistryEditForm):
    schema = IElevateSettings
    label = _(
        "solr_elevate_configuration_label",
        default="Solr Push Elevate Configuration",
    )

    fields = field.Fields(IElevateSettings)


class ElevateSettingsView(ControlPanelFormWrapper):
    form = ElevateSettingsEditForm
