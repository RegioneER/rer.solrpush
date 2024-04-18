# -*- coding: utf-8 -*-
from plone.restapi.controlpanels.interfaces import IControlpanel
from zope.publisher.interfaces.browser import IDefaultBrowserLayer


class IRerSolrpushLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""


class IRERSolrpushRestapiControlpanel(IControlpanel):
    """
    Marker interface for controlpanel
    """
