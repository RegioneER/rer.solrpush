# -*- coding: utf-8 -*-
from plone import api
from Products.Five.browser import BrowserView
from zope.interface import implementer
from zope.publisher.interfaces import IPublishTraverse

import six


class SolrScalesHandler(BrowserView):
    """
    View callable on SolrBrain contents that mimic @@images.
    """

    def tag(
        self,
        fieldname=None,
        scale=None,
        css_class="",
        alt=None,
        title=None,
        direction="thumbnail",
        loading="lazy",
        **args,
    ):
        if not title:
            title = self.context.Title
        if not alt:
            alt = self.context.Description or self.context.Title

        if six.PY2:
            title = title.encode("utf-8")
            alt = alt.encode("utf-8")

        # needed for cache invalidation
        date = self.context.modified.strftime("%Y%m%d%H%M%S")

        html = '<img src="{url}/@@images/{fieldname}/{scale}?direction={direction}&v={date}" alt="{alt}" title="{title}" loading="{loading}"'.format(
            url=self.context.getURL(),
            fieldname=fieldname or "image",
            scale=scale or "thumb",
            alt=alt,
            title=title,
            loading=loading,
            direction=direction,
            date=date,
        )
        if css_class:
            html += ' class="{}"'.format(css_class)
        if args:
            for key, value in sorted(args.items()):
                if value:
                    html += ' {}="{}"'.format(key, value)
        html += ">"
        return html


@implementer(IPublishTraverse)
class SolrImages(BrowserView):
    def __init__(self, context, request):
        super(SolrImages, self).__init__(context, request)
        self.name = ""
        self.scale = ""

    def publishTraverse(self, request, name):
        self.name = name
        stack = request.get("TraversalRequestNameStack")
        if stack:
            self.scale = stack.pop()
        return self

    def __call__(self):
        direction = self.request.form.get("direction", "thumbnail")
        scales = api.content.get_view(
            name="images", context=self.context, request=self.request
        )

        return self.request.response.redirect(
            scales.scale(self.name, scale=self.scale, direction=direction).url
        )
