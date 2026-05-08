# -*- coding: utf-8 -*-
"""Utilities for syncing Plone catalog fields to the Solr managed schema."""

from plone import api
from plone.api.exc import InvalidParameterError
from rer.solrpush.interfaces.adapter import IAdditionalSolrSkipFields
from rer.solrpush.utils.solr_common import get_setting
from rer.solrpush.utils.solr_common import is_solr_active
from zope.component import getUtilitiesFor

import logging
import requests

logger = logging.getLogger(__name__)

# Fields handled explicitly (not indexed, computed or loaded dynamically).
# Add-ons can extend this list through registry and/or utilities.
SKIP_CATALOG_FIELDS = {
    "id",  # explicit field in Solr schema
    "path",  # computed directly from physical path
    "path_depth",  # computed directly from physical path
    "path_parents",  # computed directly from physical path
    "site_name",  # computed via get_site_title()
    "url",  # computed via absolute_url()
    "view_name",  # computed via getLayout()
    "last_comment_date",
    "listCreators",
    "nav_title",
    "parent",
    "Type",
    "allowedRolesAndUsers",
    "cmf_uid",
    "exclude_from_nav",
    "is_default_page",
    "object_provides",
    "sortable_title",
}

# Metadata field names that are known to be dates.
# Used by metadata sync to determine the field type (pdate).
DATE_METADATA_FIELDS = {
    "CreationDate",
    "EffectiveDate",
    "ExpirationDate",
    "ModificationDate",
}

# Catalog index type → Solr field type mapping.
INDEX_TYPE_MAPPING = {
    "DateIndex": "pdate",
    "DateRangeIndex": "pdate",
    "BooleanIndex": "boolean",
    "ZCTextIndex": "text_general",
    "KeywordIndex": "string",
    "FieldIndex": "string",
    "ExtendedPathIndex": "string",
    "SetOperationIndex": "string",
}

# Catalog index meta_types that contain multiple values.
MULTIVALUE_INDEX_TYPES = {
    "KeywordIndex",
    "ExtendedPathIndex",
    "SetOperationIndex",
    "ZCTextIndex",
}


def _get_field_type_for_metadata(field_name):
    """Determine the Solr field type for a metadata-only column.

    Returns 'pdate' for known date metadata fields, 'string' for others.
    """
    if field_name in DATE_METADATA_FIELDS:
        return "pdate"
    return "string"


def _normalize_field_names(values):
    if not values:
        return set()
    if isinstance(values, str):
        values = values.replace("\n", ",").split(",")

    normalized = set()
    for value in values:
        if value is None:
            continue
        item = str(value).strip()
        if item:
            normalized.add(item)
    return normalized


def _get_registry_skip_fields():
    try:
        values = get_setting(field="excluded_catalog_fields") or []
    except InvalidParameterError:
        # Backward compatibility: record may be missing before upgrade step.
        logger.warning(
            "rer.solrpush: missing registry record 'excluded_catalog_fields'; "
            "using empty list (run upgrade step to 3600)."
        )
        values = []
    return _normalize_field_names(values)


def _get_adapter_skip_fields():
    fields = set()
    for name, utility in getUtilitiesFor(IAdditionalSolrSkipFields):
        try:
            extra = utility.get_fields()
        except Exception as err:  # pragma: no cover
            logger.warning(
                "rer.solrpush: failed reading extra skip fields from utility '%s': %s",
                name,
                err,
            )
            continue
        fields.update(_normalize_field_names(extra))
    return fields


def get_effective_skip_fields():
    """Return built-in + registry + utility skip fields."""
    skip_fields = set(SKIP_CATALOG_FIELDS)
    skip_fields.update(_get_registry_skip_fields())
    skip_fields.update(_get_adapter_skip_fields())
    return skip_fields


def _build_catalog_index_spec(field_name, index_obj):
    index_meta_type = getattr(index_obj, "meta_type", type(index_obj).__name__)
    return {
        "name": field_name,
        "type": INDEX_TYPE_MAPPING.get(index_meta_type, "string"),
        "stored": True,
        "indexed": True,
        "multiValued": index_meta_type in MULTIVALUE_INDEX_TYPES,
    }


def _build_metadata_field_spec(field_name):
    return {
        "name": field_name,
        "type": _get_field_type_for_metadata(field_name),
        "stored": True,
        "indexed": False,
        "multiValued": True,
    }


def _defaulted_field_value(field, key):
    defaults = {
        "stored": True,
        "indexed": True,
        "multiValued": False,
    }
    return field.get(key, defaults.get(key))


def _needs_replace(existing_field, desired_field):
    if existing_field.get("type") != desired_field.get("type"):
        return True
    for key in ("stored", "indexed", "multiValued"):
        if bool(_defaulted_field_value(existing_field, key)) != bool(
            desired_field.get(key)
        ):
            return True
    return False


def _validate_solr_api_response(resp, endpoint):
    resp.raise_for_status()
    try:
        payload = resp.json()
    except ValueError as err:
        raise ValueError("Invalid JSON received from Solr %s" % endpoint) from err

    header = payload.get("responseHeader")
    if not isinstance(header, dict):
        raise ValueError(
            "Invalid Solr response from %s: missing responseHeader" % endpoint
        )

    status = header.get("status")
    if status != 0:
        raise ValueError(
            "Solr %s returned non-zero status (%s): %s"
            % (endpoint, status, payload.get("error") or payload)
        )

    return payload


def _fetch_solr_fields(solr_url):
    resp = requests.get(solr_url + "schema/fields", timeout=10)
    payload = _validate_solr_api_response(resp, "schema/fields")

    fields = payload.get("fields", [])
    if not isinstance(fields, list):
        raise ValueError("Invalid Solr response: 'fields' is not a list")
    return {field["name"]: field for field in fields}


def _sync_fields(solr_url, desired_specs):
    existing_fields = _fetch_solr_fields(solr_url)

    fields_to_add = []
    fields_to_replace = []
    for spec in desired_specs:
        existing = existing_fields.get(spec["name"])
        if existing is None:
            fields_to_add.append(spec)
            continue
        if _needs_replace(existing, spec):
            fields_to_replace.append(spec)

    if fields_to_add:
        resp = requests.post(
            solr_url + "schema",
            json={"add-field": fields_to_add},
            timeout=30,
        )
        _validate_solr_api_response(resp, "schema add-field")

    for spec in fields_to_replace:
        resp = requests.post(
            solr_url + "schema",
            json={"replace-field": spec},
            timeout=30,
        )
        _validate_solr_api_response(resp, "schema replace-field")

    return len(fields_to_add), len(fields_to_replace)


def get_metadata_only_fields():
    """Return the set of catalog metadata columns that are NOT catalog indexes
    and are not handled explicitly elsewhere.

    These are columns stored in the catalog brain but not searchable via
    catalog queries (i.e., no corresponding index). They need to be explicitly
    added to the Solr schema so they can be stored and returned in search
    results.
    """
    catalog = api.portal.get_tool(name="portal_catalog")
    catalog_indexes = set(catalog.Indexes.keys())
    catalog_metadata = set(catalog.schema())
    return catalog_metadata - catalog_indexes - get_effective_skip_fields()


def _get_solr_computed_fields():
    """Return Solr field specs for computed/extra fields not in catalog.

    These fields are computed directly in create_index_dict:
    - path: catalog physical path as string
    - path_depth: depth of path
    - path_parents: list of path components
    - view_name: layout name
    - url: absolute URL
    - @id, @type: REST API field copies
    """
    return [
        {
            "name": "path",
            "type": "string",
            "stored": True,
            "indexed": True,
            "multiValued": False,
        },
        {
            "name": "path_depth",
            "type": "string",
            "stored": True,
            "indexed": True,
            "multiValued": False,
        },
        {
            "name": "path_parents",
            "type": "string",
            "stored": True,
            "indexed": True,
            "multiValued": True,
        },
        {
            "name": "view_name",
            "type": "string",
            "stored": True,
            "indexed": False,
            "multiValued": False,
        },
        {
            "name": "url",
            "type": "string",
            "stored": True,
            "indexed": False,
            "multiValued": False,
        },
        {
            "name": "@id",
            "type": "string",
            "stored": True,
            "indexed": False,
            "multiValued": False,
        },
        {
            "name": "@type",
            "type": "string",
            "stored": True,
            "indexed": False,
            "multiValued": False,
        },
    ]


def sync_metadata_fields_to_solr():
    """Sync Solr schema for all catalog indexes and metadata columns.

    - catalog indexes are created as indexed fields
    - metadata-only columns are created as stored-only fields
    - built-in skip list can be extended from registry and adapter utilities
    """
    if not is_solr_active():
        return

    solr_url = get_setting(field="solr_url")
    if not solr_url:
        return

    if not solr_url.endswith("/"):
        solr_url = solr_url + "/"

    catalog = api.portal.get_tool(name="portal_catalog")
    skip_fields = get_effective_skip_fields()
    catalog_indexes = catalog.Indexes

    index_specs = []
    for field_name, index_obj in sorted(catalog_indexes.items()):
        if field_name in skip_fields:
            continue
        index_specs.append(_build_catalog_index_spec(field_name, index_obj))

    metadata_only = sorted(
        set(catalog.schema()) - set(catalog_indexes.keys()) - set(skip_fields)
    )
    metadata_specs = [
        _build_metadata_field_spec(field_name) for field_name in metadata_only
    ]

    # Add computed Solr fields (path, url, etc.)
    computed_specs = _get_solr_computed_fields()

    desired_specs = index_specs + metadata_specs + computed_specs
    if not desired_specs:
        return

    try:
        added_count, replaced_count = _sync_fields(solr_url, desired_specs)
    except (requests.exceptions.RequestException, ValueError, KeyError) as err:
        logger.error("rer.solrpush: failed to sync Solr schema fields: %s", err)
        return

    logger.info(
        "rer.solrpush: Solr schema sync completed (indexes=%d, metadata=%d, "
        "added=%d, replaced=%d, skipped=%d)",
        len(index_specs),
        len(metadata_specs),
        added_count,
        replaced_count,
        len(skip_fields),
    )
