# -*- coding: utf-8 -*-
from plone import api
from rer.solrpush import _
from rer.solrpush.interfaces import IElevateSettings
from zope.i18n import translate
from rer.solrpush.utils.solr_common import get_solr_connection
from rer.solrpush.utils.solr_common import get_setting
from rer.solrpush.utils.solr_common import get_index_fields
from rer.solrpush.interfaces.settings import IRerSolrpushSettings
from rer.solrpush.utils.solr_indexer import parse_date_str
from DateTime import DateTime
from pysolr import safe_urlencode
from zope.annotation.interfaces import IAnnotations
from zope.globalrequest import getRequest

import logging
import json
import re
import requests
import six


logger = logging.getLogger(__name__)

TRIM = re.compile(r"\s+")
ESCAPE_CHARS_RE = re.compile(r'(?<!\\)(?P<char>[&|+\-!(){}[\]^"~*?:])')

# HELPER METHODS


def fix_value(value, index_type="", wrap=True):
    operator = "or"
    if isinstance(value, dict):
        query = value.get("query", "")
        range = value.get("range", "")
        operator = value.get("operator", "or")
        if not query:
            return ""
        if range:
            if range == "min":
                value = "[{} TO *]".format(parse_date_str(query))
            if range == "max":
                value = "[* TO {}]".format(parse_date_str(query))
            if range == "minmax":
                value = "[{} TO {}]".format(
                    parse_date_str(query[0]), parse_date_str(query[1])
                )
            return value
        else:
            value = query
    if isinstance(value, DateTime):
        return "[{} TO *]".format(parse_date_str(value))
    if isinstance(value, six.string_types):
        if index_type == "date":
            if "TO" not in value:
                return "[{} TO *]".format(parse_date_str(value))
            else:
                return value
        return escape_special_characters(value, wrap)
    elif isinstance(value, list):
        join_str = " {} ".format(operator.upper())
        return "({})".format(
            join_str.join([escape_special_characters(x, wrap) for x in value])
        )
    logger.warning(
        "[fix_value]: unable to escape value: {}. skipping".format(value)
    )
    return


def escape_special_characters(value, wrap):
    new_value = ESCAPE_CHARS_RE.sub(r"\\\g<char>", value)
    if six.PY2 and isinstance(new_value, six.string_types):
        try:
            new_value = new_value.encode("utf-8")
        except UnicodeDecodeError:
            pass
    if wrap:
        return '"{}"'.format(new_value)
    return new_value


def set_sort_parameter(query):
    sort_on = query.get("sort_on")
    if sort_on == "sortable_title":
        sort_on = "Title"
    sort_order = query.get("sort_order", "asc")
    if sort_order in ["reverse", "descending"]:
        sort_order = "desc"
    if sort_order in ["ascending"]:
        sort_order = "asc"
    return "{sort_on} {sort_order}".format(
        sort_on=sort_on, sort_order=sort_order
    )


def generate_query(
    query,
    fl=None,
    facets=False,
    facet_fields=["Subject", "portal_type"],
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
    if "sort_on" in query:
        solr_query["sort"] = set_sort_parameter(query)
    if facets:
        solr_query["facet.field"] = facet_fields
        solr_query["facet.mincount"] = 1
        solr_query["facet.limit"] = -1
    if fl:
        if "UID" not in fl:
            # we need it because if we ask for [elevated] value, solr returns
            # error if we don't ask also the primary key
            if isinstance(fl, six.text_type):
                fl = "{} UID".format(fl)
            elif isinstance(fl, list):
                fl.append("UID")
        solr_query["fl"] = fl

    solr_query.update(add_query_tweaks())
    # elevate
    elevate = manage_elevate(query=query)
    if elevate.get("enableElevation", False):
        solr_query.update(manage_elevate(query=query))
        if "fl" not in solr_query:
            solr_query["fl"] = "* [elevated]"
        else:
            if "[elevated]" not in solr_query["fl"]:
                if isinstance(solr_query["fl"], six.text_type):
                    solr_query["fl"] = "{} [elevated]".format(solr_query["fl"])
                elif isinstance(solr_query["fl"], list):
                    solr_query["fl"].append("[elevated]")
    return solr_query


def manage_elevate(query):
    params = {}
    params["enableElevation"] = "false"
    searchableText = query.get("SearchableText", "").rstrip("*")
    if not searchableText:
        return params
    if not searchableText.replace(" ", ""):
        return params
    elevate_schema = extract_elevate_schema(query=query)

    if not elevate_schema:
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
        for config in elevate_schema:
            # exact match
            # if text == s:

            # contains
            # if s in text:

            # contains regexp
            for word in config.get("text", []):
                if re.search("(^|\s+)" + word + "(\s+|$)", text):  # noqa
                    uids = [x.get("UID", "") for x in config.get("uid", [])]
                    params["enableElevation"] = "true"
                    params["elevateIds"] = ",".join(uids)
                    break
    return params


def extract_elevate_schema(query):
    """
    If no site_name is passed in query and remote_elevate_schema is set,
    return the schema from remote site.
    """
    local_schema_json = get_setting(
        field="elevate_schema", interface=IElevateSettings
    )
    remote_schema = get_setting(
        field="remote_elevate_schema", interface=IRerSolrpushSettings
    )

    # if local_schema is set and there is a filter on site_name, return the
    # local elevate schema
    if local_schema_json:
        local_schema = json.loads(local_schema_json)
        if local_schema:
            if query.get("site_name", []):
                return local_schema
            if not remote_schema:
                return local_schema
    if remote_schema:
        try:
            resp = requests.get(
                remote_schema, headers={"Accept": "application/json"}
            )
        except requests.exceptions.RequestException as err:
            logger.error("Connection problem:\n{0}".format(err))
            return []
        if resp.status_code != 200:
            logger.error(
                "Problems fetching schema:\n{0}\n{1}".format(
                    resp.status_code, resp.reason
                )
            )
            return []
        return resp.json()
    return []


def extract_from_query(query):
    index_fields = get_index_fields()
    params = {"q": "", "fq": []}
    for index, value in query.items():
        if not value:
            continue
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
        value = fix_value(value=value, index_type=index_infos.get("type", ""))
        if value:
            if index == "path":
                index = "path_parents"
            params["fq"].append(
                "{index}:{value}".format(index=index, value=value)
            )
    can_access_inactive = api.user.has_permission(
        "Access inactive portal content"
    )
    if not can_access_inactive:
        # do not show expired or not yet published items
        if "expires" not in query:
            params["fq"].append("expires:[NOW TO *]")
        if "effective" not in query:
            params["fq"].append("effective:[* TO NOW]")
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
    fl=None,
    facets=False,
    facet_fields=["Subject", "portal_type"],
    **kwargs
):
    """[summary] TODO

    Args:
        query ([type]): [description] TODO
        fl (str, optional): [description]. Defaults to "".
        facets (bool, optional): [description]. Defaults to False.
        facet_fields (list, optional): [description].
        Defaults to ["Subject", "portal_type"].

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
    )
    try:
        _set_query_debug(solr=solr, params=solr_query)
        res = solr.search(**solr_query)
        return res
    except Exception as e:
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


def _set_query_debug(solr, params):
    try:
        if not get_setting(
            field="query_debug", interface=IRerSolrpushSettings
        ):
            return
    except KeyError:
        # key not available: do not save data
        return
    request = getRequest()
    annotations = IAnnotations(request)
    annotations["solr_query"] = {
        "url": "{url}/select?{params}".format(
            url=solr.url, params=safe_urlencode(params, True)
        ),
        "params": params,
    }
