============
rer.solrpush
============

.. image:: https://github.com/RegioneER/rer.solrpush/workflows/Tests/badge.svg


Product that allows SOLR indexing/searching of a Plone website.


Control Panel
-------------

- Active: flag to enable/disable SOLR integration
- Solr URL: SOLR core url
- Portal types to index in SOLR
- Public frontend url


Hidden registry fields
''''''''''''''''''''''

There are some "service" registry fields hidden to disallow users to edit them.

- ready: a flag that specifies if the product is ready/initialized.
  It basically indicates that schema.xml has been loaded.
- index_fields: is the list of SOLR fields loaded from schema.xml file.


schema.xml load
'''''''''''''''

SOLR fields are directly read from `schema.xml` file exposed by SOLR.

This schema is stored in Plone registry for performance reasons
and is always synced when you save `solr-controlpanel` form
or click on `Reload schema.xml` button.

Search configuration
''''''''''''''''''''

In solr controlpanel (*/@@solrpush-conf*) there are some field that allows admins to setup some query parameters.

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


Development buildout
--------------------

In the buildout there is a solr configuration (in `conf` folder) and a recipe that builds a solr instance locally.

To use it, simply run::

    > ./bin/solr-foreground



Search
------

Date fields:

from DateTime import DateTime
timezone = DateTime().timezone()
DateTime(value).toZone(timezone).ISO8601()


Installation
------------

Add rer.solrpush to buildout::

    [buildout]

    ...

    eggs =
        rer.solrpush


and run ``bin/buildout`` command.


Contribute
----------

- Issue Tracker: https://github.com/RegioneER/rer.solrpush/issues
- Source Code: https://github.com/RegioneER/rer.solrpush

Compatibility
-------------

This product has been tested on Plone 5.1 and 5.2


Credits
-------

Developed with the support of `Regione Emilia Romagna`__;

Regione Emilia Romagna supports the `PloneGov initiative`__.

__ http://www.regione.emilia-romagna.it/
__ http://www.plonegov.it/

Authors
-------

This product was developed by RedTurtle Technology team.

.. image:: http://www.redturtle.net/redturtle_banner.png
   :alt: RedTurtle Technology Site
   :target: http://www.redturtle.net/
