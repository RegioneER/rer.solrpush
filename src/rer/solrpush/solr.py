# -*- coding: utf-8 -*-
from DateTime import DateTime
from lxml import etree
from plone import api
from plone.indexer.interfaces import IIndexableObject
from plone.registry.interfaces import IRegistry
from pysolr import SolrError
from rer.solrpush import _
from rer.solrpush.interfaces.settings import IRerSolrpushSettings
from rer.solrpush.restapi.services.solr_search.batch import DEFAULT_BATCH_SIZE
from zope.component import getUtility
from zope.component import queryMultiAdapter
from zope.i18n import translate

import logging
import pysolr
import requests
import six
import json
import re
from six.moves import map

if six.PY2:
    from ftfy import fix_text

try:
    # rer.agidtheme overrides site tile field
    from rer.agidtheme.base.interfaces import IRERSiteSchema as ISiteSchema
    from rer.agidtheme.base.utility.interfaces import ICustomFields

    RER_THEME = True
except ImportError:
    from Products.CMFPlone.interfaces.controlpanel import ISiteSchema

    RER_THEME = False

logger = logging.getLogger(__name__)

ADDITIONAL_FIELDS = ["searchwords"]

LUCENE_SPECIAL_CHARACTERS = '+-&|!(){}^"~?:\t\v\\/'


def fix_value(value, wrap=True):
    if isinstance(value, six.string_types):
        return escape_special_characters(value, wrap)
    elif isinstance(value, list):
        return "({})".format(
            " OR ".join([escape_special_characters(x, wrap) for x in value])
        )
        # return list(map(escape_special_characters, value))
    logger.warning("[fix_value]: unable to escape value: {}. skipping".format(value))
    return


ESCAPE_CHARS_RE = re.compile(r'(?<!\\)(?P<char>[&|+\-!(){}[\]^"~*?:])')


def escape_special_characters(value, wrap):
    new_value = ESCAPE_CHARS_RE.sub(r"\\\g<char>", value)
    # if ('OR' not in new_value or 'AND' not in new_value) and ' ' in new_value:
    #     new_value = '"{}"'.format(new_value)
    if wrap:
        return '"{}"'.format(new_value)
    return new_value


def get_setting(field):
    return api.portal.get_registry_record(
        field, interface=IRerSolrpushSettings, default=False
    )


def set_setting(field, value):
    return api.portal.set_registry_record(
        field, interface=IRerSolrpushSettings, value=value
    )


def get_index_fields(field):
    json_str = api.portal.get_registry_record(
        field, interface=IRerSolrpushSettings, default=""
    )
    return json.loads(json_str)


def get_site_title():
    registry = getUtility(IRegistry)
    site_settings = registry.forInterface(ISiteSchema, prefix="plone", check=False)
    site_title = getattr(site_settings, "site_title") or ""
    if RER_THEME:
        fields_value = getUtility(ICustomFields)
        site_title = fields_value.titleLang(site_title)
    if six.PY2:
        site_title = site_title.decode("utf-8")
    return site_title


def get_solr_connection(context=None, **kwargs):
    # TODO: fix sporadic
    # ResourceWarning: Enable tracemalloc to get the object allocation traceback
    # ResourceWarning: unclosed <socket.socket ... raddr=('127.0.0.1', 8983)>
    # -> avoid explicit close connection

    # XXX: rivalutare il default True per always_commit !
    if "always_commit" not in kwargs:
        kwargs["always_commit"] = True
    is_ready = get_setting(field="ready")
    solr_url = get_setting(field="solr_url")
    if not is_ready or not solr_url:
        return
    if context is None:
        context = api.portal.get()
    if context is None:
        client = pysolr.Solr(solr_url, **kwargs)
    else:
        jar = getattr(context, "_p_jar", None)
        oid = getattr(context, "_p_oid", None)
        if jar is None or oid is None:
            # object is not persistent or is not yet associated with a
            # connection
            cache = context._v_solr_client_cache = {}
        else:
            cache = getattr(jar, "foreign_connections", None)
            if cache is None:
                cache = jar.foreign_connections = {}
        cache_key = "solr_%s_%s" % (solr_url, kwargs)
        client = cache.get(cache_key)
        if client is None:
            client = cache[cache_key] = pysolr.Solr(solr_url, **kwargs)
    return client


def parse_date_as_datetime(value):
    """Sistemiamo le date"""
    if value:
        format = "%Y-%m-%dT%H:%M:%S"
        return value.utcdatetime().strftime(format) + "Z"
    return value


def parse_date_str(value):
    return parse_date_as_datetime(DateTime(value))


def init_solr_push():
    """Inizializza la voce di registro 'index_fields'

    Lo fa leggendo il file xml di SOLR.

    :param solr_url: [required] L'url a cui richiedere il file xml
    :type solr_url: string
    :returns: Empty String if everything's good
    :rtype: String
    """
    solr_url = get_setting(field="solr_url")

    if solr_url:
        if not solr_url.endswith("/"):
            solr_url = solr_url + "/"
        try:
            respo = requests.get(solr_url + "admin/file?file=schema.xml")
        except requests.exceptions.RequestException as err:
            ErrorMessage = "Connection problem:\n{0}".format(err)
            return ErrorMessage
        if respo.status_code != 200:
            ErrorMessage = "Problems fetching schema:\n{0}\n{1}".format(
                respo.status_code, respo.reason
            )
            return ErrorMessage

        root = etree.fromstring(respo.content)
        chosen_fields = json.dumps(extract_fields(nodes=root.findall(".//field")))
        if six.PY2:
            chosen_fields = chosen_fields.decode("utf-8")
        set_setting(field="index_fields", value=chosen_fields)
        set_setting(field="ready", value=True)
        set_setting(field="active", value=True)
        return

    return _("No SOLR url provided")


def extract_fields(nodes):
    fields = {}
    for node in nodes:
        field_name = node.get("name")
        field_type = node.get("type")
        if six.PY2:
            field_name = six.text_type(field_name)
            field_type = six.text_type(field_type)
        fields[field_name] = {"type": field_type}
    return fields


def is_solr_active():
    """Just checking if solr indexing is set to active in control panel"""
    return get_setting(field="active")


def is_right_portal_type(item):
    enabled_types = get_setting(field="enabled_types")
    if not enabled_types:
        return True
    return item.portal_type in enabled_types


def can_index(item):
    """Check if the item passed as argument can and has to be indexed"""
    with api.env.adopt_roles(["Anonymous"]):
        if not api.user.has_permission("View", obj=item):
            return False
    if not is_solr_active():
        return False
    return is_right_portal_type(item)


def create_index_dict(item):
    """Restituisce un dizionario pronto per essere 'mandato' a SOLR per
    l'indicizzazione.
    """

    index_fields = get_index_fields(field="index_fields")
    frontend_url = get_setting(field="frontend_url")

    catalog = api.portal.get_tool(name="portal_catalog")
    adapter = queryMultiAdapter((item, catalog), IIndexableObject)
    index_me = {}

    for field in index_fields.keys():
        field_infos = index_fields[field]
        field_type = field_infos.get("type")
        if six.PY2:
            field = field.encode("ascii")
        value = getattr(adapter, field, None)
        if not value:
            continue
        if callable(value):
            value = value()
        if six.PY2:
            value = fix_py2_strings(value)
        if isinstance(value, DateTime):
            value = parse_date_as_datetime(value)
        else:
            if field_type == "date":
                value = parse_date_str(value)
        index_me[field] = value

    for field in ADDITIONAL_FIELDS:
        value = getattr(item, field, None)
        if value is not None:
            index_me[field] = value
    portal = api.portal.get()
    index_me["site_name"] = get_site_title()
    index_me["path"] = "/".join(item.getPhysicalPath())
    index_me["path_depth"] = len(item.getPhysicalPath()) - 2
    if frontend_url:
        index_me["url"] = item.absolute_url().replace(portal.portal_url(), frontend_url)
    else:
        index_me["url"] = item.absolute_url()
    return index_me


def fix_py2_strings(value):
    """ REMOVE ON PYTHON 3 """
    if isinstance(value, six.string_types):
        if not isinstance(value, six.text_type):
            value = value.decode("utf-8")
        return fix_text(value)
    if isinstance(value, list):
        return list(map(fix_py2_strings, value))
    if isinstance(value, tuple):
        return tuple(map(fix_py2_strings, value))
    return value


def set_sort_parameter(query):
    sort_on = query.get("sort_on")
    sort_order = query.get("sort_order", "asc")
    if sort_order in ["reverse"]:
        return "{sort_on} desc".format(sort_on=sort_on)
    return "{sort_on} {sort_order}".format(sort_on=sort_on, sort_order=sort_order)


def generate_query(
    query,
    fl="",
    facets=False,
    facet_fields=["Subject", "portal_type"],
    filtered_sites=[],
    **kwargs
):
    index_fields = get_index_fields(field="index_fields")
    # index_ids = [x['id'] for x in index_fields]
    solr_query = kwargs
    solr_query.update(
        {
            "q": "",
            "fq": [],
            "facet": facets and "true" or "false",
            "start": query.get("b_start", 0),
            "rows": query.get("b_size", DEFAULT_BATCH_SIZE),
            "json.nl": "arrmap",
        }
    )
    for index, value in query.items():
        if index == "*":
            solr_query["q"] = "*:*"
            continue
        if index == "":
            solr_query["q"] = fix_value(value, wrap=False)
            continue
        index_infos = index_fields.get(index, {})
        if not index_infos:
            continue
        if index == "SearchableText":
            solr_query["q"] = u"SearchableText:{}".format(
                fix_value(value=value, wrap=False)
            )
        else:
            if index_infos.get("type") not in ["date"]:
                value = fix_value(value=value)
            solr_query["fq"].append("{index}:{value}".format(index=index, value=value))
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
    return solr_query


def push_to_solr(item_or_obj):
    """
    Perform push to solr
    """
    solr = get_solr_connection()
    if not solr:
        logger.error("Unable to push to solr. Configuration is incomplete.")
        return
    if not isinstance(item_or_obj, dict):
        if can_index(item_or_obj):
            item_or_obj = create_index_dict(item_or_obj)
        else:
            item_or_obj = None
    if item_or_obj:
        solr.add([item_or_obj])
        return True
    else:
        return False


def remove_from_solr(uid):
    """
    Perform remove item from solr
    """
    if not is_solr_active():
        return
    solr = get_solr_connection()
    portal = api.portal.get()
    if not solr:
        logger.error("Unable to push to solr. Configuration is incomplete.")
        return
    try:
        solr.delete(q="UID:{}".format(uid), commit=True)
    except (pysolr.SolrError, TypeError) as err:
        logger.error(err)
        message = _(
            "content_remove_error",
            default=u"There was a problem removing this content from SOLR. "
            " Please contact site administrator.",
        )
        api.portal.show_message(message=message, request=portal.REQUEST, type="error")


def reset_solr():
    solr = get_solr_connection()
    if not solr:
        logger.error("Unable to push to solr. Configuration is incomplete.")
        return
    solr.delete(q='site_name:"{}"'.format(get_site_title()), commit=True)


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
        facet_fields (list, optional): [description]. Defaults to ["Subject", "portal_type"].
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
        **kwargs
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
