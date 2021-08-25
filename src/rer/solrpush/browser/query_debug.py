# -*- coding: utf-8 -*-
from plone.app.layout.viewlets.common import ViewletBase
from zope.annotation.interfaces import IAnnotations


class QueryDebug(ViewletBase):
    def update(self):
        self.query = self.get_query()

    def get_query(self):
        annotations = IAnnotations(self.request)
        return annotations.get("solr_query", "")
