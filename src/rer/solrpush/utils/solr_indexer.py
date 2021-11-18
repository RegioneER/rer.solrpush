# -*- coding: utf-8 -*-
from DateTime import DateTime
from plone import api
from plone.indexer.interfaces import IIndexableObject
from plone.registry.interfaces import IRegistry
from rer.solrpush import _
from rer.solrpush.interfaces.adapter import IExtractFileFromTika
from six.moves import map
from zope.component import getUtility
from zope.component import queryMultiAdapter
from rer.solrpush.utils.solr_common import get_solr_connection
from rer.solrpush.utils.solr_common import get_setting
from rer.solrpush.utils.solr_common import get_index_fields
from rer.solrpush.utils.solr_common import is_solr_active
from rer.solrpush.utils.solr_common import should_force_commit

import datetime
import logging
import pysolr
import six


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

RESTAPI_METADATA_FIELDS = ["@id", "@type", "description", "title"]

# HELPER METHODS


def get_site_title():
    registry = getUtility(IRegistry)
    site_settings = registry.forInterface(
        ISiteSchema, prefix="plone", check=False
    )
    site_title = getattr(site_settings, "site_title") or ""
    if RER_THEME:
        site_subtitle_style = (
            getattr(site_settings, "site_subtitle_style") or ""
        )
        fields_value = getUtility(ICustomFields)
        site_title = fields_value.titleLang(site_title)
        site_subtitle = fields_value.subtitleLang(
            getattr(site_settings, "site_subtitle") or "{}"
        )
        if site_subtitle and site_subtitle_style == "subtitle-normal":
            site_title += " {}".format(site_subtitle)

    if six.PY2:
        site_title = site_title.decode("utf-8")
    return site_title


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
    return is_right_portal_type(item)


def create_index_dict(item):
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

    # extra-catalog schema
    index_me["site_name"] = get_site_title()
    index_me["path"] = "/".join(item.getPhysicalPath())
    index_me["path_depth"] = len(item.getPhysicalPath()) - 2
    index_me["attachment"] = attachment_to_index(item)
    index_me["getIcon"] = False
    if "view_name" in index_fields.keys():
        index_me["view_name"] = item.getLayout()

    # convert url to frontend one
    if frontend_url:
        index_me["url"] = item.absolute_url().replace(
            portal.portal_url(), frontend_url
        )
    else:
        index_me["url"] = item.absolute_url()

    has_image = getattr(item.aq_base, "image", None)
    if has_image:
        index_me["getIcon"] = True

    return index_me


def fix_py2_strings(value):
    """ REMOVE ON PYTHON 3 """
    if isinstance(value, six.string_types):
        if not isinstance(value, six.text_type):
            value = value.replace("\xc0?", "").decode("utf-8", "ignore")
        return fix_text(value)
    if isinstance(value, list):
        return list(map(fix_py2_strings, value))
    if isinstance(value, tuple):
        return tuple(map(fix_py2_strings, value))
    return value


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
            "literal.{key}".format(key=key): encode_strings_for_attachments(
                value
            )
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
    if not isinstance(item_or_obj, dict):
        if can_index(item_or_obj):
            item_or_obj = create_index_dict(item_or_obj)
        else:
            item_or_obj = None
    if not item_or_obj:
        return False
    attachment = item_or_obj.pop("attachment", None)
    if attachment:
        add_with_attachment(
            solr=solr, attachment=attachment, fields=item_or_obj
        )
    else:
        solr.add(docs=[item_or_obj], commit=should_force_commit())
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
        solr.delete(
            q="UID:{}".format(uid), commit=should_force_commit(),
        )
    except (pysolr.SolrError, TypeError) as err:
        logger.error(err)
        message = _(
            "content_remove_error",
            default=u"There was a problem removing this content from SOLR. "
            " Please contact site administrator.",
        )
        api.portal.show_message(
            message=message, request=portal.REQUEST, type="error"
        )


def reset_solr():
    solr = get_solr_connection()
    if not solr:
        logger.error("Unable to push to solr. Configuration is incomplete.")
        return
    solr.delete(
        q='site_name:"{}"'.format(get_site_title()),
        commit=should_force_commit(),
    )
