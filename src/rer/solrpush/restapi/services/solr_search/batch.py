# -*- coding: utf-8 -*-
from plone.restapi.deserializer import json_body
from six.moves.urllib.parse import parse_qsl
from six.moves.urllib.parse import urlencode


DEFAULT_BATCH_SIZE = 25


class SolrHypermediaBatch(object):
    def __init__(self, request, results):
        self.request = request

        self.b_start = int(
            json_body(self.request).get("b_start", False)
        ) or int(self.request.form.get("b_start", 0))
        self.b_size = int(json_body(self.request).get("b_size", False)) or int(
            self.request.form.get("b_size", DEFAULT_BATCH_SIZE)
        )

        self.hits = getattr(results, "hits", 0)

    @property
    def canonical_url(self):
        """Return the canonical URL to the batched collection-like resource,
        preserving query string params, but stripping all batching related
        params from it.
        """
        url = self.request["ACTUAL_URL"]
        qs_params = parse_qsl(self.request["QUERY_STRING"])

        # Remove any batching / sorting related parameters.
        # Also take care to preserve list-like query string params.
        for key, value in qs_params[:]:
            if key in (
                "b_size",
                "b_start",
                "sort_on",
                "sort_order",
                "sort_limit",
            ):
                qs_params.remove((key, value))

        qs = urlencode(qs_params)

        if qs_params:
            url = "?".join((url, qs))
        return url

    @property
    def current_batch_url(self):
        url = self.request["ACTUAL_URL"]
        qs = self.request["QUERY_STRING"]
        if qs:
            url = "?".join((url, qs))
        return url

    @property
    def links(self):
        """Get a dictionary with batching links.
        """
        # Don't provide batching links if resultset isn't batched
        if self.hits <= self.b_size:
            return None

        links = {}

        last = self._last_page()
        next = self._next_page()
        prev = self._prev_page()

        links["@id"] = self.current_batch_url
        links["first"] = self._url_for_batch(0)
        links["last"] = self._url_for_batch(last)

        if next:
            links["next"] = self._url_for_batch(next)

        if prev:
            links["prev"] = self._url_for_batch(prev)

        return links

    def _url_for_batch(self, pagenumber):
        """Return a new Batch object for the given pagenumber.
        """
        new_start = pagenumber * self.b_size
        return self._url_with_params(params={"b_start": new_start})

    def _last_page(self):
        page = self.hits / self.b_size
        if self.hits % self.b_size == 0:
            return page - 1
        return page

    def _next_page(self):
        curr_page = self.b_start / self.b_size
        if curr_page == self._last_page():
            return None
        return curr_page + 1

    def _prev_page(self):
        curr_page = self.b_start / self.b_size
        if curr_page == 0:
            return None
        return curr_page - 1

    def _url_with_params(self, params):
        """Build an URL based on the actual URL of the current request URL
        and add or update some query string parameters in it.
        """
        url = self.request["ACTUAL_URL"]
        qs_params = parse_qsl(
            self.request["QUERY_STRING"], keep_blank_values=1
        )

        # Take care to preserve list-like query string arguments (same QS
        # param repeated multiple times). In other words, don't turn the
        # result of parse_qsl into a dict!

        # Drop params to be updated, then prepend new params in order
        qs_params = [x for x in qs_params if x[0] not in list(params)]
        qs_params = sorted(params.items()) + qs_params

        qs = urlencode(qs_params)

        if qs_params:
            url = "?".join((url, qs))
        return url
