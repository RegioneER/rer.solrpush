# -*- coding: utf-8 -*-
from Products.Five.browser import BrowserView

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
        **args
    ):
        if not title:
            title = self.context.Title
        if not alt:
            alt = self.context.Description or self.context.Title

        if six.PY2:
            title = title.encode("utf-8")
            alt = alt.encode("utf-8")
        html = '<img src="{url}/@@images/{fieldname}/{scale}" alt="{alt}" title="{title}"'.format(
            url=self.context.getURL(),
            fieldname=fieldname or "image",
            scale=scale or "thumb",
            alt=alt,
            title=title,
        )
        if css_class:
            html += ' class="{}"'.format(css_class)
        if args:
            for key, value in sorted(args.items()):
                if value:
                    html += ' {}="{}"'.format(key, value)
        html += ">"
        return html
