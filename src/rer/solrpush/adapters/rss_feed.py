# -*- coding: utf-8 -*-
from Products.CMFPlone.browser.syndication.adapters import BaseItem
from Products.CMFPlone.interfaces.syndication import IFeed
from Products.CMFPlone.interfaces.syndication import IFeedItem
from rer.solrpush.interfaces.adapter import ISolrBrain
from zope.component import adapter
from zope.interface import implementer


@implementer(IFeedItem)
@adapter(ISolrBrain, IFeed)
class SOLRFeedItem(BaseItem):

    @property
    def link(self):
        return self.context.getURL()

    @property
    def title(self):
        return self.context.Title

    @property
    def description(self):
        return self.context.Description

    @property
    def rights(self):
        return ""
