# -*- coding: utf-8 -*-
from plone.app.contentlisting.interfaces import IContentListingObject
from zope.interface import Interface


class IExtractFileFromTika(Interface):
    def extract_from_tika(self, file_name, file_obj):
        """Call solr Tika to extract text from given file
        @return: extracted plain text
        """


class IAdditionalSolrSkipFields(Interface):
    def get_fields(self):
        """Return an iterable of catalog field names to exclude from Solr sync.

        Add-ons can register a utility providing this interface to extend the
        built-in skip list used by solr schema synchronization.
        """


class ISolrBrain(IContentListingObject):
    """ """
