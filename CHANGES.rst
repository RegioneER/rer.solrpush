Changelog
=========


1.0.0 (2021-12-20)
------------------

- Fix elevate logic.
  [cekk]
- Add invariant validation for elevate.
  [cekk]


0.8.0 (2021-11-18)
------------------

- SolrBrains now can return img tags if the original content has an image.
  [cekk]


0.7.1 (2021-10-14)
------------------

- Removed unused view.
  [cekk]

0.7.0 (2021-10-14)
------------------

- Add new criteria: solr_portal_types to select a list of portal_types indexed on SOLR.
  [cekk]
- Add link to Elevate control panel also in user actions.
  [cekk]
- Fix remote elevate conditions.
  [cekk]

0.6.4 (2021-09-27)
------------------

- Fix how querybuilder create queries.
  [cekk]


0.6.3 (2021-09-21)
------------------

- Add new feature: if "Query debug" flag is enabled in settings, the SOLR query will be shown to managers.
  [cekk]
- In example schema.xml files (dev and test), set "searchwords" as **lowercase** type, to be case insensitive.
  [cekk]
- Disable facet.limit default value (100) to get all facets.
  [cekk]
- Use swallow_duplicates in Keywords vocabulary to avoid duplicated tokens by truncated strings by SimpleTerm init.
  [cekk]

0.6.2 (2021-07-15)
------------------

- Do not escape queries in querybuilder because solr_search already manage them.
  [cekk]


0.6.1 (2021-06-10)
------------------

- [fix] now sort_on is not ignored on querybuilder customization.
  [cekk]
- [fix] remove / from frontend_url when not needed in indexing.
  [cekk]


0.6.0 (2021-05-20)
------------------

- Add criteria for search by Subject stored in SOLR.
  [cekk]
- Now solr brains also return right content-type icon.
  [cekk]  

0.5.1 (2021-04-29)
------------------

- Fix release.
  [cekk]


0.5.0 (2021-04-20)
------------------

- Handle all possible exceptions on search call.
  [cekk]
- Fix encodings (again) for attachement in POST calls.
  [cekk]
- Handle multilanguage paths in querybuilder for collections (use navigation root path instead portal path).
  [cekk]

0.4.1 (2021-03-26)
------------------

- Fix encodings for attachement in POST calls.
  [cekk]


0.4.0 (2021-03-25)
------------------

- Handle encodings for attachement POST calls.
  [cekk]


0.3.4 (2021-03-18)
------------------

- Fix logs.
  [cekk]


0.3.3 (2021-03-15)
------------------

- Make immediate commits optional from control panel.
  [cekk]


0.3.2 (2021-02-15)
------------------

- Handle simple datetmie dates.
  [cekk]


0.3.1 (2021-02-11)
------------------

- Fix tika indexing parameters: now modified and created dates are correctly indexed.
  [cekk]


0.3.0 (2021-02-09)
------------------

- Refactor elevate control panel and use collective.z3cform.jsonwidget.
  [cekk]
- Some improvements in indexing.
  [cekk]


0.2.4 (2021-01-28)
------------------

- Fix logic in maintenance view.
  [cekk]


0.2.3 (2021-01-27)
------------------

- Fix maintenance sync view.
  [cekk]

0.2.2 (2020-12-14)
------------------

- Fix encoding problems in `escape_special_characters` method for python2.
  [cekk]
- Remove collective.z3cform.datagrifield dependency and temporary disable elevate control panel.
  [cekk]

0.2.1 (2020-12-03)
------------------

- Fix date indexes in query when they already are in "solr syntax".
  [cekk]


0.2.0 (2020-12-03)
------------------

- Add styles for elevate widget
  [nzambello]
- Refactor indexer logic.
  [mamico]
- Add support for *bq* and *qf* in search.
  [mamico]
- Index files with tika.
  [cekk]
- Add support for collections.
  [cekk]
- Mute noisy solr logs in maintenance.
  [cekk]

0.1.2 (2019-12-12)
------------------

- Remove noisy logger for queries.
  [cekk]


0.1.1 (2019-12-12)
------------------

- Add new index: path_depth
  [cekk]
- Fix unicode errors when there is a site name with accents.
  [cekk]

0.1.0 (2019-12-05)
------------------

- Initial release.
  [cekk]
