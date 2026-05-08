# -*- coding: utf-8 -*-
from plone import api
from rer.solrpush import _
from rer.solrpush.interfaces.settings import IRerSolrpushSettings

import pysolr
import requests


def get_setting(field, interface=IRerSolrpushSettings):
    return api.portal.get_registry_record(field, interface=interface, default=False)


def set_setting(field, value, interface=IRerSolrpushSettings):
    return api.portal.set_registry_record(field, interface=interface, value=value)


def is_solr_active():
    """Just checking if solr indexing is set to active in control panel"""
    return get_setting(field="active")


def should_force_commit():
    return get_setting(field="force_commit") or False


def check_solr_connection():
    """Verify that the configured SOLR instance is reachable.

    :returns: None if everything is fine, an error message string otherwise.
    """
    solr_url = get_setting(field="solr_url")
    if not solr_url:
        return _("No SOLR url provided")
    if not solr_url.endswith("/"):
        solr_url = solr_url + "/"
    try:
        resp = requests.get(solr_url + "admin/ping", timeout=5)
    except requests.exceptions.RequestException as err:
        return "Connection problem:\n{0}".format(err)
    if resp.status_code != 200:
        return "SOLR ping failed:\n{0}\n{1}".format(resp.status_code, resp.reason)
    return None


# Backward-compatible alias kept for any external code still calling init_solr_push().
# Deprecated: use check_solr_connection() instead.
init_solr_push = check_solr_connection


def get_solr_connection(context=None, **kwargs):
    # TODO: fix sporadic
    # ResourceWarning: Enable tracemalloc to get the object allocation traceback
    # ResourceWarning: unclosed <socket.socket ... raddr=('127.0.0.1', 8983)>
    # -> avoid explicit close connection

    # XXX: rivalutare il default True per always_commit !
    if "always_commit" not in kwargs:
        kwargs["always_commit"] = True
    solr_url = get_setting(field="solr_url")
    if not is_solr_active() or not solr_url:
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
