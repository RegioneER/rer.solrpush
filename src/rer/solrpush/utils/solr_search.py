# -*- coding: utf-8 -*-
from plone import api
from pysolr import SolrError
from rer.solrpush import _
from rer.solrpush.interfaces import IElevateSettings
from zope.i18n import translate
from rer.solrpush.utils.solr_common import get_solr_connection
from rer.solrpush.utils.solr_common import get_setting
from rer.solrpush.utils.solr_common import get_index_fields

import logging
import re
import six


logger = logging.getLogger(__name__)

TRIM = re.compile(r"\s+")
ESCAPE_CHARS_RE = re.compile(r'(?<!\\)(?P<char>[&|+\-!(){}[\]^"~*?:])')

# HELPER METHODS


def fix_value(value, wrap=True):
    if isinstance(value, six.string_types):
        return escape_special_characters(value, wrap)
    elif isinstance(value, list):
        return "({})".format(
            " OR ".join([escape_special_characters(x, wrap) for x in value])
        )
        # return list(map(escape_special_characters, value))
    logger.warning(
        "[fix_value]: unable to escape value: {}. skipping".format(value)
    )
    return


def escape_special_characters(value, wrap):
    new_value = ESCAPE_CHARS_RE.sub(r"\\\g<char>", value)
    # if ('OR' not in new_value or 'AND' not in new_value) and ' ' in new_value:  # noqa
    #     new_value = '"{}"'.format(new_value)
    if wrap:
        return '"{}"'.format(new_value)
    return new_value


def set_sort_parameter(query):
    sort_on = query.get("sort_on")
    sort_order = query.get("sort_order", "asc")
    if sort_order in ["reverse"]:
        return "{sort_on} desc".format(sort_on=sort_on)
    return "{sort_on} {sort_order}".format(
        sort_on=sort_on, sort_order=sort_order
    )


def generate_query(
    query,
    fl="",
    facets=False,
    facet_fields=["Subject", "portal_type"],
    filtered_sites=[],
):
    solr_query = {
        "q": "",
        "fq": [],
        "facet": facets and "true" or "false",
        "start": query.get("b_start", 0),
        "rows": query.get("b_size", 20),
        "json.nl": "arrmap",
    }
    solr_query.update(extract_from_query(query=query))

    if not solr_query["q"]:
        solr_query["q"] = "*:*"
    if filtered_sites:
        if six.PY2:
            sites = [u'"{}"'.format(x) for x in filtered_sites]
        else:
            sites = ['"{}"'.format(x) for x in filtered_sites]
        solr_query["fq"].append(u"site_name:({})".format(" OR ".join(sites)))
    if "sort_on" in query:
        solr_query["sort"] = set_sort_parameter(query)
    if facets:
        solr_query["facet.field"] = facet_fields
    if fl:
        solr_query["fl"] = fl

    solr_query.update(add_query_tweaks())
    # elevate
    solr_query.update(manage_elevate(query))
    return solr_query


def manage_elevate(query):
    params = {}
    params["enableElevation"] = "false"
    searchableText = query.get("SearchableText", "")
    if not searchableText:
        return params
    if not searchableText.replace(" ", ""):
        return params
    elevate_map = get_setting(
        field="elevate_schema", interface=IElevateSettings
    )
    if not elevate_map:
        return params
    try:
        if six.PY2:
            text = (
                TRIM.sub(" ", searchableText).strip().decode("utf-8").lower()
            )
        else:
            text = TRIM.sub(" ", searchableText).strip().lower()
    except Exception:
        logger.exception("error parsing %r", searchableText)
        text = None
    if text:
        for config in elevate_map:
            # exact match
            # if text == s:

            # contains
            # if s in text:

            # contains regexp
            for word in config.get("text", []):
                if re.search("(^|\s+)" + word + "(\s+|$)", text):  # noqa
                    params["enableElevation"] = "true"
                    params["elevateIds"] = ",".join(config.get("uid", []))
                    break
    return params


def extract_from_query(query):
    index_fields = get_index_fields(field="index_fields")
    params = {"q": "", "fq": []}
    for index, value in query.items():
        if index == "*":
            params["q"] = "*:*"
            continue
        if index in ["", "SearchableText"]:
            params["q"] = fix_value(value, wrap=False)

            continue
        index_infos = index_fields.get(index, {})
        if not index_infos:
            continue
        # other indexes will be added in fq
        if index_infos.get("type") not in ["date"]:
            value = fix_value(value=value)
        params["fq"].append("{index}:{value}".format(index=index, value=value))
    return params


def add_query_tweaks():
    """
    Add query tweaks set in control panel
    """
    params = {}
    for id in ["qf", "bq", "bf"]:
        value = get_setting(field=id)
        if value:
            params[id] = value
    if params:
        params["defType"] = "edismax"
    return params


# END HELPER METHODS

# LIBRARY METHODS
def search(
    query,
    fl="",
    facets=False,
    facet_fields=["Subject", "portal_type"],
    filtered_sites=[],
    **kwargs
):
    """[summary] TODO

    Args:
        query ([type]): [description] TODO
        fl (str, optional): [description]. Defaults to "".
        facets (bool, optional): [description]. Defaults to False.
        facet_fields (list, optional): [description].
        Defaults to ["Subject", "portal_type"].
        filtered_sites (list, optional): [description]. Defaults to [].

    Returns:
        [type]: [description]
    """
    solr = get_solr_connection()
    if not solr:
        msg = u"Unable to search using solr. Configuration is incomplete."
        logger.error(msg)
        return {
            "error": True,
            "message": translate(
                _("solr_configuration_error_label", default=msg),
                context=api.portal.get().REQUEST,
            ),
        }
    solr_query = generate_query(
        query,
        fl=fl,
        facets=facets,
        facet_fields=facet_fields,
        filtered_sites=filtered_sites,
    )
    try:
        res = solr.search(**solr_query)
        return res
    except SolrError as e:
        logger.exception(e)
        return {
            "error": True,
            "message": translate(
                _(
                    "search_error_label",
                    default=u"Unable to perform a search with SOLR."
                    u" Please contact the site administrator or wait some"
                    u" minutes.",
                ),
                context=api.portal.get().REQUEST,
            ),
        }
