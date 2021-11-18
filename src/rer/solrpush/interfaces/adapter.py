# -*- coding: utf-8 -*-
from zope.interface import Interface


class IExtractFileFromTika(Interface):
    def extract_from_tika(self, file_name, file_obj):
        """ Call solr Tika to extract text from given file
        @return: extracted plain text
        """


class ISolrBrain(Interface):
    """ """
