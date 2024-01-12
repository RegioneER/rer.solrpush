# -*- coding: utf-8 -*-
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from plone.restapi.controlpanels.interfaces import IControlpanel


class IRerSolrpushLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""


class IRERSolrpushRestapiControlpanel(IControlpanel):
    """
    Marker interface for controlpanel
    """
