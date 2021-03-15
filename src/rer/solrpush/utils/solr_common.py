# -*- coding: utf-8 -*-
from lxml import etree
from plone import api
from rer.solrpush import _
from rer.solrpush.interfaces.settings import IRerSolrpushSettings

import json
import pysolr
import requests
import six


def get_setting(field, interface=IRerSolrpushSettings):
    return api.portal.get_registry_record(
        field, interface=interface, default=False
    )


def set_setting(field, value, interface=IRerSolrpushSettings):
    return api.portal.set_registry_record(
        field, interface=interface, value=value
    )


def is_solr_active():
    """Just checking if solr indexing is set to active in control panel"""
    return get_setting(field="active")


def should_force_commit():
    return get_setting(field="force_commit") or False


def get_index_fields():
    json_str = get_setting(field="index_fields")
    return json.loads(json_str)


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
        chosen_fields = json.dumps(
            extract_fields(nodes=root.findall(".//field"))
        )
        if six.PY2:
            chosen_fields = chosen_fields.decode("utf-8")
        set_setting(field="index_fields", value=chosen_fields)
        set_setting(field="ready", value=True)
        return

    return _("No SOLR url provided")


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
