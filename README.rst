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

File indexing
'''''''''''''

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
