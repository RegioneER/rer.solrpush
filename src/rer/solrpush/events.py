# -*- coding: utf-8 -*-
"""Event handlers for rer.solrpush."""

from rer.solrpush.interfaces.settings import IRerSolrpushSettings
from rer.solrpush.utils.solr_common import get_setting
from rer.solrpush.utils.solr_common import is_solr_active
from rer.solrpush.utils.solr_schema import sync_metadata_fields_to_solr

import logging

logger = logging.getLogger(__name__)

# Registry record names that, when modified, should trigger a metadata schema sync.
_TRIGGER_FIELDS = {
    f"{IRerSolrpushSettings.__identifier__}.active",
    f"{IRerSolrpushSettings.__identifier__}.solr_url",
    f"{IRerSolrpushSettings.__identifier__}.excluded_catalog_fields",
}


def on_registry_record_modified(event):
    """Sync catalog metadata columns to the Solr schema when the add-on is
    activated or when the Solr URL is changed.

    This subscriber listens to ``IRecordModifiedEvent`` from
    ``plone.app.registry`` and fires ``sync_metadata_fields_to_solr()``
    whenever the ``active`` flag or ``solr_url`` registry records are changed,
    provided that, after the change, Solr is active and a URL is configured.
    """
    record = event.record
    record_name = record.__name__

    if record_name not in _TRIGGER_FIELDS:
        return

    # After the change, check whether Solr is now active and has a URL.
    if not is_solr_active():
        return
    if not get_setting(field="solr_url"):
        return

    logger.info(
        "rer.solrpush: registry record '%s' changed, syncing metadata "
        "fields to Solr schema.",
        record_name,
    )
    sync_metadata_fields_to_solr()
