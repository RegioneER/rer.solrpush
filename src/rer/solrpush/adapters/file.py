# -*- coding: utf-8 -*-
from rer.solrpush.interfaces.adapter import IExtractFileFromTika
from zope.interface import implementer


@implementer(IExtractFileFromTika)
class FileExtractor(object):
    def __init__(self, context):
        self.context = context

    def get_file_to_index(self):
        """
        """
        if not self.context.file:
            return ""
        return self.context.file.data
