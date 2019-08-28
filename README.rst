.. This README is meant for consumption by humans and pypi. Pypi can render rst files so please do not use Sphinx features.
   If you want to learn more about writing documentation, please check out: http://docs.plone.org/about/documentation_styleguide.html
   This text does not appear on pypi or github. It is a comment.

============
rer.solrpush
============

Prodotto per il push delle modifiche di un sito regionale su SOLR per
ottimizzare l'indicizzazione.


Control Panel
-------------

- Active: specifica se il push deve essere effettuato
- Solr URL: l'indirizzo a cui connettersi a SOLR
- Site ID
- Portal types da indicizzare
- Configurazione elevate
- Flag debug query solr


Campi del registro nascosti
'''''''''''''''''''''''''''

Ci sono degli altri campi del registro che però non sono visibili dal pannello
di controllo in modo che non vengano modificati per sbaglio.

- ready: un flag che specifica se il prodotto è pronto/inizializzato ed è
  usabile. Principalmente segnala se lo schema.xml è stato caricato da SOLR ed
  è stato parsato
- index_fields: è una lista di stringhe dei vari field/attributi da indicizzare.
  Questa lista viene popolata leggendo direttamente il file schema.xml del solr
  regionale


Caricamento schema.xml
''''''''''''''''''''''

I campi da indicizzare su SOLR li leggiamo direttamente dal file `schema.xml`
che SOLR stesso espone (ed è proprio il suo file di configurazione).

Dopo aver inserito l'url di SOLR (e aver salvato il form), cliccare sul
bottone "Load schema.xml".

Le logiche di questo caricamento e parsing dell'xml sono all'interno del form
del pannello di controllo del prodotto (`RerSolrpushEditForm`).
Non le abbiamo messe in altri punti del transaction manager che andiamo ad
aggiungere perchè altrimenti ci saremmo ritrovati *nel mezzo* di una transazione
e non avremmo potuto apportare modifiche al registry.


Ricerca
-------

Campi data:

from DateTime import DateTime
timezone = DateTime().timezone()
DateTime(value).toZone(timezone).ISO8601()


Examples
--------

This add-on can be seen in action at the following sites:
- Is there a page on the internet where everybody can see the features?


Documentation
-------------

Full documentation for end users can be found in the "docs" folder, and is also available online at http://docs.plone.org/foo/bar


Translations
------------

This product has been translated into

- Klingon (thanks, K'Plai)


Installation
------------

Install rer.solrpush by adding it to your buildout::

    [buildout]

    ...

    eggs =
        rer.solrpush


and then running ``bin/buildout``


Contribute
----------

- Issue Tracker: https://github.com/collective/rer.solrpush/issues
- Source Code: https://github.com/collective/rer.solrpush
- Documentation: https://docs.plone.org/foo/bar


Support
-------

If you are having issues, please let us know.
We have a mailing list located at: project@example.com


License
-------

The project is licensed under the GPLv2.
