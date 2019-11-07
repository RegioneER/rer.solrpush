# -*- coding: utf-8 -*-
from Products.Five import BrowserView
from rer.solrpush.solr import search


class View(BrowserView):
    def __call__(self):
        search(self.request.form)
