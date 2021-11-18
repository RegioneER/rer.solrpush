============
rer.solrpush
============

.. image:: https://github.com/RegioneER/rer.solrpush/workflows/Tests/badge.svg

Product that allows SOLR indexing/searching of a Plone website.

SOLR schema configuration
=========================

This product works with some assumptions and SOLR schema need to have some particular configuration.

You can see an example in config folder of this product.

By default we mapped all base Plone indexes/metadata into SOLR, plus some additional fields::

    <field name="searchwords" type="string" indexed="true" stored="true" required="false" multiValued="true" termVectors="false" termPositions="false" termOffsets="false"/>
    <field name="showinsearch" type="boolean" indexed="true" stored="false" required="false" multiValued="false" termVectors="false" termPositions="false" termOffsets="false"/>
    <field name="url" type="string" indexed="false" stored="true" required="false" multiValued="false" termVectors="false" termPositions="false" termOffsets="false"/>
    <field name="site_name" type="string" indexed="true" stored="true" required="false" multiValued="false" termVectors="false" termPositions="false" termOffsets="false"/>
    <field name="path_depth" type="pint" indexed="false" stored="true" required="false" multiValued="false" termVectors="false" termPositions="false" termOffsets="false"/>
    <field name="path_parents" type="string" indexed="true" stored="true" multiValued="true"/>
    <field name="view_name" type="string" indexed="true" stored="true" required="false" multiValued="false" termVectors="false" termPositions="false" termOffsets="false"/>
    <field name="@id" type="string" indexed="false" stored="true" required="false" multiValued="false" termVectors="false" termPositions="false" termOffsets="false"/>
    <field name="@type" type="string" indexed="false" stored="true" required="false" multiValued="false" termVectors="false" termPositions="false" termOffsets="false"/>
    <field name="title" type="text_it" indexed="false" stored="true" required="false" multiValued="false" termVectors="false" termPositions="false" termOffsets="false"/>

- `searchwords`, `view_name`, `path_parents`, `path_depth`, `site_name` are needed for query filter and boost (see below)
- `showinsearch` is needed to allow/disallow single content indexing
- `url` is an index where we store frontend url
- `@id`, `@type` and `title` are needed for plone.restapi-like responses

plone.restapi related metadata are not indexed from Plone, but they are copied in SOLR::

    <copyField source="Title" dest="title"/>
    <copyField source="portal_type" dest="@type"/>
    <copyField source="url" dest="@id"/>


Control Panel
=============

- Active: flag to enable/disable SOLR integration
- Solr URL: SOLR core url
- Portal types to index in SOLR
- Public frontend url


Hidden registry fields
----------------------

There are some "service" registry fields hidden to disallow users to edit them.

- ready: a flag that specifies if the product is ready/initialized.
  It basically indicates that schema.xml has been loaded.
- index_fields: is the list of SOLR fields loaded from schema.xml file.


schema.xml load
---------------

SOLR fields are directly read from `schema.xml` file exposed by SOLR.

This schema is stored in Plone registry for performance reasons
and is always synced when you save `solr-controlpanel` form
or click on `Reload schema.xml` button.

File indexing
-------------

If Tika is configured on SOLR, you can send attachments to it and they will be indexed as SearchableText in the content.

To allow attachments indexing, you need to register an adapter for each content-type that you need to index.

`File` content-type is already registered, so you can copy from that::

    <adapter
      for="plone.app.contenttypes.interfaces.IFile"
      provides="rer.solrpush.interfaces.adapter.IExtractFileFromTika"
      factory=".file.FileExtractor"
      />

::

    from rer.solrpush.interfaces.adapter import IExtractFileFromTika
    from zope.interface import implementer


    @implementer(IExtractFileFromTika)
    class FileExtractor(object):
        def __init__(self, context):
            self.context = context

        def get_file_to_index(self):
            """
            """
            here you need to return the file that need to be indexed

N.B.: `SearchableText` index should be **multivalued**.


Search configuration
--------------------

In solr controlpanel (*/@@solrpush-settings*) there are some field that allows admins to setup some query parameters.

'qf' specifies a list of fields, each of which is assigned a boost factor to increase
or decrease that particular field’s relevance in the query.

For example if you want to give more relevance to results that contains searched
text into their title than in the text, you could set something like this::

    title^1000.0 SearchableText^1.0 description^500.0

You can also elevate by *searchwords*.

`bq` specifies an additional, optional, query clause that will be added to the user’s main query to influence the score.
For example if we want to boost results that have a specific `searchwords` term::

    searchwords:something^1000
  
Solr will improve ranking for results that have "*something*" in their searchwords field.

`bf` specifies functions (with optional boosts) that will be used to construct FunctionQueries
which will be added to the user’s main query as optional clauses that will influence the score.
Any `function supported natively <https://lucene.apache.org/solr/guide/6_6/function-queries.html>`_ by Solr can be used, along with a boost value.
For example if we want to give less relevance to items deeper in the tree we can set something like this::

    recip(path_depth,10,100,1)

*path_depth* is an index that counts tree level of an object.

Collections
===========

There are two new Collection's criteria that allows to search on SOLR also in Collections:

- *Search with SOLR*: if checked, searches will be redirected to SOLR (the default is always on local Plone Site).
- *Sites*: a list of indexes plone sites on SOLR. The user can select on which sites perform the query.
  If no sites are set (or this criteria not selected), the default search will be made only in the current site.

There is also a customized querybuilder that perform queries to SOLR or to Plone catalog.

Results from SOLR are wrapped into some brain-like objects to be fully compatible with Collection views.


Development buildout
====================

In the buildout there is a solr configuration (in `conf` folder) and a recipe that builds a solr instance locally.

To use it, simply run::

    > ./bin/solr-foreground


Installation
============

Add rer.solrpush to buildout::

    [buildout]

    ...

    eggs =
        rer.solrpush


and run ``bin/buildout`` command.


Contribute
==========

- Issue Tracker: https://github.com/RegioneER/rer.solrpush/issues
- Source Code: https://github.com/RegioneER/rer.solrpush

Compatibility
=============

This product has been tested on Plone 5.1 and 5.2


Credits
=======

Developed with the support of `Regione Emilia Romagna`__;

Regione Emilia Romagna supports the `PloneGov initiative`__.

__ http://www.regione.emilia-romagna.it/
__ http://www.plonegov.it/

Authors
=======

This product was developed by RedTurtle Technology team.

.. image:: http://www.redturtle.net/redturtle_banner.png
   :alt: RedTurtle Technology Site
   :target: http://www.redturtle.net/
