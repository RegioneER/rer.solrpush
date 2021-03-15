Changelog
=========


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
