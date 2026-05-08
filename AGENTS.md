# Copilot Instructions for rer.solrpush

## Project Overview

`rer.solrpush` is a Plone add-on (namespace package: `rer.solrpush`) that integrates Apache Solr indexing and searching into a Plone 6 site. It replaces the default `@search` REST API endpoint with a Solr-backed implementation and hooks into Plone's content indexing pipeline. Targets **Solr 9.x** (managed schema / schemaless mode).

## Build & Test Commands

This project uses **buildout** for running tests and **tox + uv** for linting.

```bash
# Bootstrap and build (after setting up buildout.cfg)
pip install -r requirements.txt -c constraints_plone60.txt
buildout -N

# Start Solr for development (Docker)
docker compose up -d

# Run all tests (requires SOLR running on port 8983)
BUILDOUT_SOLR_ENVIRONMENT=true bin/test

# Run a single test by name
BUILDOUT_SOLR_ENVIRONMENT=true bin/test -t test_events

# Run tests matching a module pattern
BUILDOUT_SOLR_ENVIRONMENT=true bin/test -s rer.solrpush -t TestSOLRPush

# Run with coverage
BUILDOUT_SOLR_ENVIRONMENT=true bin/test-coverage

# Linting via tox (requires: uv tool install tox --with tox-uv)
tox -e black          # check formatting
tox -e black-apply    # auto-format
tox -e flake8         # lint
tox -e zpretty        # check ZCML formatting
tox -e zpretty-apply  # auto-format ZCML
tox -e pyroma         # package metadata quality
tox                   # run all checks
```

Tests require a running Solr instance at `http://localhost:8983/solr/solrpush_test`. The `BUILDOUT_SOLR_ENVIRONMENT=true` env var triggers the test layer to start/stop Solr via `bin/solr-start` and `bin/solr-stop`.

## Architecture

### Indexing pipeline

Content changes in Plone flow through:

1. **`indexer.py` — `SolrIndexProcessor`**: A `IIndexQueueProcessor` utility that queues index/reindex/unindex operations per-request and flushes them in `commit()`. `check_attributes()` uses `catalog.indexes()` to decide whether a partial reindex affects Solr-relevant fields.
2. **`utils/solr_indexer.py` — `push_to_solr` / `remove_from_solr`**: Performs the actual Solr operations using `pysolr`. `create_index_dict()` builds the document by iterating all `portal_catalog` indexes via `IIndexableObject` adapters. Date values are serialized via `_serialize_value()`.
3. **`utils/solr_common.py` — `get_solr_connection`**: Returns a cached `pysolr.Solr` client, keyed per ZODB connection. `check_solr_connection()` performs a Solr ping to verify connectivity.

### Solr 9 managed schema (schemaless mode)

Solr 9 uses a **managed schema**: fields are auto-created on first document submission. There is no `schema.xml` to parse:

- **No `index_fields` registry record**: the old per-field type cache has been removed. Field discovery is done at runtime via `portal_catalog.Indexes`.
- **No `ready` flag**: connection validity is checked with a ping (`check_solr_connection()`), not a schema load.
- **`create_index_dict()` flow**: iterates `catalog.indexes()`, skips fields in `SKIP_CATALOG_FIELDS` (`path`, `path_depth`, `path_parents`), then appends computed Solr-specific fields (`path`, `path_depth`, `path_parents`, `site_name`, `url`, `view_name`, `@id`, `@type`, `title`, `description`).
- **Date serialization**: `_serialize_value()` detects `DateTime` / `datetime.date` / `datetime.datetime` values and converts to Solr ISO-8601 UTC strings. In search (`solr_search.py`) and parser (`parser.py`), date indexes are detected by checking `catalog.Indexes[name].meta_type in {"DateIndex", "DateRangeIndex"}`.

### Search

The `@search` plone.restapi endpoint is overridden in `restapi/services/solr_search/` by `SearchGet`, which delegates to `SolrSearchHandler` when `search_enabled` is True in the registry. `extract_from_query()` filters query params to known `portal_catalog` indexes (plus a small set of Solr-specific extras).

### Settings

All configuration is stored in the **Plone registry** under `IRerSolrpushSettings` (which extends `IRerSolrpushConf` + `IRerSolrpushSearchConf` in `interfaces/settings.py`). Access settings via:

```python
from rer.solrpush.utils.solr_common import get_setting
value = get_setting(field="active")

# Or directly:
from plone import api
from rer.solrpush.interfaces.settings import IRerSolrpushSettings
api.portal.get_registry_record("active", interface=IRerSolrpushSettings)
```

### File attachment indexing (Tika)

Register an `IExtractFileFromTika` adapter for your content type. See `adapters/file.py` for the `File` type example. `attachment_to_index()` in `solr_indexer.py` calls the adapter; if it returns a file object, the content is sent to Solr's `/update/extract` endpoint.

### Testing layer

`testing.py` defines:
- `SolrLayer`: starts/stops the Solr process
- `RerSolrpushRestApiLayer`: extends `PloneRestApiDXLayer`, installs the add-on profile, sets `active=True`
- Functional tests use `RER_SOLRPUSH_API_FUNCTIONAL_TESTING` (wraps `ZSERVER_FIXTURE`)
- Integration tests use `RER_SOLRPUSH_API_INTEGRATION_TESTING`

## Key Conventions

- **Browser layer guard**: `SolrIndexProcessor.active` checks `IRerSolrpushLayer.providedBy(request)` — Solr indexing only fires when the layer is present (i.e., the add-on is installed in the site).
- **`can_index()` gate**: Before indexing, always check `can_index(obj)` which verifies: anonymous View permission, Solr active, correct portal type, and `exclude_from_search` not set.
- **Commit strategy**: Controlled by `force_commit` registry setting. Use `should_force_commit()` when calling `solr.add()` or `solr.delete()`. Disable for SolrCloud/ZooKeeper setups.
- **isort profile**: `plone` (configured in both `setup.cfg` and `pyproject.toml`).
- **black target**: `py38`.
- **i18n domain**: `rer.solrpush` — use the `_()` message factory from `rer.solrpush.__init__` for translatable strings.
- **GenericSetup profiles**: `default`, `uninstall`, and upgrade step profiles (`to_1100`, `to_1300`, etc.) live under `profiles/`. Current version: **3500**.

## Project Overview

`rer.solrpush` is a Plone add-on (namespace package: `rer.solrpush`) that integrates Apache Solr indexing and searching into a Plone 6 site. It replaces the default `@search` REST API endpoint with a Solr-backed implementation and hooks into Plone's content indexing pipeline.

## Build & Test Commands

This project uses **buildout**, not pip/tox directly for running tests.

```bash
# Bootstrap and build (after setting up buildout.cfg)
pip install -r requirements.txt -c constraints_plone60.txt
buildout -N

# Run all tests (requires SOLR running on port 8983)
BUILDOUT_SOLR_ENVIRONMENT=true bin/test

# Run a single test by name
BUILDOUT_SOLR_ENVIRONMENT=true bin/test -t test_events

# Run tests matching a module pattern
BUILDOUT_SOLR_ENVIRONMENT=true bin/test -s rer.solrpush -t TestSOLRPush

# Run with coverage
BUILDOUT_SOLR_ENVIRONMENT=true bin/test-coverage

# Code analysis (flake8 + isort + zpretty)
bin/code-analysis

# Linting individually
black src/ --check --diff
flake8 src/
isort --check-only --recursive src/
```

Tests require a running Solr instance at `http://localhost:8983/solr/solrpush_test`. The `BUILDOUT_SOLR_ENVIRONMENT=true` env var triggers the test layer to start/stop Solr via `bin/solr-start` and `bin/solr-stop`.

For development, start Solr locally with:
```bash
./bin/solr-foreground
```

## Architecture

### Indexing pipeline

Content changes in Plone flow through:

1. **`indexer.py` — `SolrIndexProcessor`**: A `IIndexQueueProcessor` utility that queues index/reindex/unindex operations per-request and flushes them in `commit()`.
2. **`utils/solr_indexer.py` — `push_to_solr` / `remove_from_solr`**: Performs the actual Solr operations using `pysolr`. `create_index_dict()` builds the document by iterating over `index_fields` (read from registry) and using `IIndexableObject` adapters.
3. **`utils/solr_common.py` — `get_solr_connection`**: Returns a cached `pysolr.Solr` client, keyed per ZODB connection to avoid leaking connections.

### Search

The `@search` plone.restapi endpoint is overridden in `restapi/services/solr_search/` by `SearchGet`, which delegates to `SolrSearchHandler` when `search_enabled` is True in the registry.

### Settings

All configuration is stored in the **Plone registry** under `IRerSolrpushSettings` (which extends `IRerSolrpushConf` + `IRerSolrpushSearchConf` in `interfaces/settings.py`). Access settings via:

```python
from rer.solrpush.utils.solr_common import get_setting
value = get_setting(field="active")

# Or directly:
from plone import api
from rer.solrpush.interfaces.settings import IRerSolrpushSettings
api.portal.get_registry_record("active", interface=IRerSolrpushSettings)
```

### SOLR schema / field mapping

On save of the control panel (or clicking "Reload schema.xml"), `init_solr_push()` fetches `{solr_url}admin/file?file=schema.xml`, parses it with lxml, and stores the field list as JSON in the registry (`index_fields`). Only fields present in this list are indexed. The `ready` flag must be `True` for any indexing to occur.

### File attachment indexing (Tika)

Register an `IExtractFileFromTika` adapter for your content type. See `adapters/file.py` for the `File` type example. `attachment_to_index()` in `solr_indexer.py` calls the adapter; if it returns a file object, the content is sent to Solr's `/update/extract` endpoint.

### Testing layer

`testing.py` defines:
- `SolrLayer`: starts/stops the Solr process
- `RerSolrpushRestApiLayer`: extends `PloneRestApiDXLayer`, installs the add-on profile, sets `active=True` and calls `init_solr_push()`
- Functional tests use `RER_SOLRPUSH_API_FUNCTIONAL_TESTING` (wraps `ZSERVER_FIXTURE`)
- Integration tests use `RER_SOLRPUSH_API_INTEGRATION_TESTING`

## Key Conventions

- **Browser layer guard**: `SolrIndexProcessor.active` checks `IRerSolrpushLayer.providedBy(request)` — Solr indexing only fires when the layer is present (i.e., the add-on is installed in the site).
- **`can_index()` gate**: Before indexing, always check `can_index(obj)` which verifies: anonymous View permission, Solr active, correct portal type, and `exclude_from_search` not set.
- **Commit strategy**: Controlled by `force_commit` registry setting. Use `should_force_commit()` when calling `solr.add()` or `solr.delete()`. Disable for SolrCloud/ZooKeeper setups.
- **`six` compatibility remnants**: Some files still import from `six` — this is legacy and being cleaned up; new code should be Python 3 only.
- **isort profile**: `plone` (configured in both `setup.cfg` and `pyproject.toml`).
- **black target**: `py38`.
- **i18n domain**: `rer.solrpush` — use the `_()` message factory from `rer.solrpush.__init__` for translatable strings.
- **GenericSetup profiles**: `default`, `uninstall`, and upgrade step profiles (`to_1100`, `to_1300`, etc.) live under `profiles/`.
