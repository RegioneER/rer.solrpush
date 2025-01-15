# -*- coding: utf-8 -*-
from DateTime import DateTime
from persistent.mapping import PersistentMapping
from plone import api
from plone.indexer.interfaces import IIndexableObject
from plone.registry.interfaces import IRegistry
from plone.restapi.serializer.converters import json_compatible
from Products.CMFPlone.interfaces.controlpanel import ISiteSchema
from rer.solrpush import _
from rer.solrpush.interfaces.adapter import IExtractFileFromTika
from rer.solrpush.utils.solr_common import get_index_fields
from rer.solrpush.utils.solr_common import get_setting
from rer.solrpush.utils.solr_common import get_solr_connection
from rer.solrpush.utils.solr_common import is_solr_active
from rer.solrpush.utils.solr_common import should_force_commit
from six.moves import map
from zope.component import getUtility
from zope.component import queryMultiAdapter
from zope.globalrequest import getRequest

import datetime
import json
import logging
import pysolr
import six


logger = logging.getLogger(__name__)

ADDITIONAL_FIELDS = [""]

RESTAPI_METADATA_FIELDS = ["@id", "@type", "description", "title"]

# HELPER METHODS


def all_site_titles():
    registry = getUtility(IRegistry)
    titles = []
    for lang in registry["plone.available_languages"]:
        title = get_site_title(lang=lang)
        if title not in titles:
            titles.append(title)
    return titles


def all_site_titles_query():
    site_titles = all_site_titles()
    query_value = ""
    if len(site_titles) == 1:
        query_value = f'"{site_titles[0]}"'
    else:
        titles = " OR ".join([f'"{x}"' for x in site_titles])
        query_value = f"({titles})"
    return query_value


def get_site_title(lang=None):
    site_props = queryMultiAdapter(
        (api.portal.get(), getRequest()), name="GET_application_json_@site"
    )()

    if site_props:
        site_props = json.loads(site_props)
        site_title = site_props.get("plone.site_title", "")
    else:
        registry = getUtility(IRegistry)
        site_settings = registry.forInterface(ISiteSchema, prefix="plone", check=False)
        site_title = getattr(site_settings, "site_title") or ""

    if isinstance(site_title, str):
        return site_title
    title_language = ""
    if lang:
        title_language = lang
    else:
        title_language = api.portal.get_current_language()

    title = site_title.get(title_language, site_title.get("default", ""))

    if not title:
        raise Exception("Unable to get site title")

    subtitle = site_props.get("plone.site_subtitle", {}).get(title_language, "")
    if subtitle:
        title = f"{title} {subtitle}"

    return title


def parse_date_as_datetime(value):
    """Sistemiamo le date"""
    if value:
        format = "%Y-%m-%dT%H:%M:%S"
        return value.utcdatetime().strftime(format) + "Z"
    return value


def parse_date_str(value):
    if isinstance(value, datetime.date):
        value = datetime.datetime.combine(value, datetime.time.min)
    return parse_date_as_datetime(DateTime(value))


def attachment_to_index(item):
    """
    If item has a provider to extract text, return the file to be indexed
    """
    try:
        provider = IExtractFileFromTika(item)
        return provider.get_file_to_index()
    except TypeError:
        return None


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
    if not is_right_portal_type(item):
        return False
    if getattr(item, "exclude_from_search", False):
        # this comes with a design.plone.contenttypes behavior
        return False
    return True


def create_index_dict(item, default={}):
    """Restituisce un dizionario pronto per essere 'mandato' a SOLR per
    l'indicizzazione.
    """
    index_fields = get_index_fields()
    frontend_url = get_setting(field="frontend_url")
    if frontend_url:
        frontend_url = frontend_url.rstrip("/")

    catalog = api.portal.get_tool(name="portal_catalog")
    adapter = queryMultiAdapter((item, catalog), IIndexableObject)
    index_me = {}
    for field, field_infos in index_fields.items():
        if field in RESTAPI_METADATA_FIELDS:
            # skip. These fields are only metadata fields needed in restap-like
            # repsonses and can be copied in solr configuration.
            continue
        field_type = field_infos.get("type")
        try:
            value = getattr(adapter, field, None)
        except Exception:
            # if we are in creation and indexing a content with a File, SearchableText
            # raise PosKeyError because it tries to read the file too, but the blob
            # isn't created yet.
            value = default.get(field, None)
        if not value and value is not False:
            continue
        if callable(value):
            value = value()
        if isinstance(value, DateTime):
            value = parse_date_as_datetime(value)
        else:
            if field_type == "date":
                value = parse_date_str(value)
        if isinstance(value, PersistentMapping):
            # convert dict-like object in json object
            value = json.dumps(json_compatible(value))
        index_me[field] = value

    for field in ADDITIONAL_FIELDS:
        value = getattr(item, field, None)
        if value is not None:
            index_me[field] = value
    portal = api.portal.get()

    # extra-catalog schema
    index_me["site_name"] = get_site_title(getattr(item, "language", ""))
    index_me["path"] = "/".join(item.getPhysicalPath())
    index_me["path_depth"] = len(item.getPhysicalPath()) - 2
    index_me["attachment"] = attachment_to_index(item)
    index_me["getIcon"] = False
    if "view_name" in index_fields.keys():
        index_me["view_name"] = item.getLayout()

    # convert url to frontend one
    if frontend_url:
        index_me["url"] = item.absolute_url().replace(portal.portal_url(), frontend_url)
    else:
        index_me["url"] = item.absolute_url()

    # backward compatibility with Plone < 6 where there wasn't image_field and image_scales indexers
    has_image = False
    if index_me.get("image_field", None) and index_me.get("image_scales", None):
        has_image = True
    else:
        has_image = getattr(item.aq_base, "image", None)
    if has_image:
        index_me["getIcon"] = True

    return index_me


def encode_strings_for_attachments(value):
    """
    Needed because attachments POST use standard requests encoding
    and not utf-8
    """
    if isinstance(value, six.string_types):
        return value.encode("ISO-8859-1", "ignore")
    if isinstance(value, list):
        return list(map(encode_strings_for_attachments, value))
    if isinstance(value, tuple):
        return tuple(map(encode_strings_for_attachments, value))
    return value


def add_with_attachment(solr, attachment, fields):
    params = {
        "extractOnly": "false",
        "lowernames": "false",
        "fmap.content": "SearchableText",
        "fmap.title": "SearchableText",
        "literalsOverride": "true",
        "commit": should_force_commit() and "true" or "false",
    }
    params.update(
        {
            "literal.{key}".format(key=key): encode_strings_for_attachments(value)
            for (key, value) in fields.items()
        }
    )
    path = "update/extract"
    return solr._send_request(
        method="post",
        path=path,
        body=params,
        files={"file": ("extracted", attachment)},
    )


# END HELPER METHODS

# LIBRARY METHODS


def push_to_solr(item_or_obj):
    """
    Perform push to solr
    """
    solr = get_solr_connection()
    if not solr:
        logger.error("Unable to push to solr. Configuration is incomplete.")
        return
    context = item_or_obj
    if isinstance(item_or_obj, dict):
        obj = api.content.get(UID=item_or_obj.get("UID", ""))
        if obj:
            context = obj
    if not can_index(context):
        return False
    index_dict = create_index_dict(item=context, default=item_or_obj)
    attachment = None
    if index_dict.get("attachment", None):
        attachment = index_dict.pop("attachment", None)
    else:
        if isinstance(item_or_obj, dict) and item_or_obj.get("attachment", None):
            attachment = item_or_obj["attachment"]
    if attachment:
        add_with_attachment(solr=solr, attachment=attachment, fields=index_dict)
    else:
        solr.add(docs=[index_dict], commit=should_force_commit())
    return True


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
        solr.delete(q=f"UID:{uid}", commit=should_force_commit())
    except (pysolr.SolrError, TypeError) as err:
        logger.error(err)
        message = _(
            "content_remove_error",
            default="There was a problem removing this content from SOLR. "
            " Please contact site administrator.",
        )
        api.portal.show_message(message=message, request=portal.REQUEST, type="warning")


def reset_solr(all=False):
    """
    Reset solr index
    """
    solr = get_solr_connection()
    if not solr:
        logger.error("Unable to push to solr. Configuration is incomplete.")
        return
    query = f"site_name:{all_site_titles_query()}"
    if all:
        query = "*:*"
    solr.delete(q=query, commit=should_force_commit())
